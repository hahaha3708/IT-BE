from pathlib import Path
from uuid import uuid4
from datetime import datetime

from django.core.files.storage import default_storage
from django.http import FileResponse
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view

from modules.accounts.models import NguoiDung
from modules.profiles.models import HoSoCongTy, HoSoUngVien
from modules.profiles.serializers import HoSoCongTySerializer, HoSoUngVienSerializer
from modules.profiles.permissions import IsCandidateSelf, IsEmployerOrCandidateSelf
from modules.profiles.pdf_generator import generate_cv_pdf
from modules.profiles.cv_templates import get_template_class


MAX_AVATAR_SIZE = 2 * 1024 * 1024
ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


class AvatarUploadRequestSerializer(serializers.Serializer):
	file = serializers.FileField(required=True)


@extend_schema_view(
	list=extend_schema(
		summary='List candidate profiles',
		tags=['profiles'],
		responses={200: HoSoUngVienSerializer(many=True)},
	),
	retrieve=extend_schema(
		summary='Get candidate profile',
		tags=['profiles'],
		responses={200: HoSoUngVienSerializer},
	),
	create=extend_schema(
		summary='Create candidate profile',
		tags=['profiles'],
		request=HoSoUngVienSerializer,
		responses={201: HoSoUngVienSerializer},
		examples=[
			OpenApiExample(
				'name',
				value={
					'ung_vien': 1,
					'ho_ten': 'Nguyen Van A',
					'avatar': 'https://cdn.example.com/avatar.jpg',
					'so_dien_thoai': '0900000000',
					'ky_nang': 'Python, Django, REST',
					'vi_tri_mong_muon': 'Backend Developer',
					'location': 'HCM',
					'thoi_gian_ranh': 'Evenings',
					'availability_slots': ['Mon-AM', 'Tue-PM'],
					'luong_mong_muon': '22000.00',
				},
				request_only=True,
			),
		],
	),
	update=extend_schema(
		summary='Replace candidate profile',
		tags=['profiles'],
		request=HoSoUngVienSerializer,
		responses={200: HoSoUngVienSerializer},
	),
	partial_update=extend_schema(
		summary='Update candidate profile partially',
		tags=['profiles'],
		request=HoSoUngVienSerializer,
		responses={200: HoSoUngVienSerializer},
	),
	destroy=extend_schema(
		summary='Delete candidate profile',
		tags=['profiles'],
		responses={204: OpenApiResponse(description='Candidate profile deleted')},
	),
)
class HoSoUngVienViewSet(viewsets.ModelViewSet):
	queryset = HoSoUngVien.objects.all()
	serializer_class = HoSoUngVienSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		"""
		Ứng viên chỉ thấy hồ sơ của chính mình.
		Nhà tuyển dụng và admin thấy tất cả hồ sơ.
		"""
		user = self.request.user
		if user.is_superuser:
			return HoSoUngVien.objects.select_related("ung_vien").all()
		
		if user.vai_tro == NguoiDung.VaiTro.UNG_VIEN:
			return HoSoUngVien.objects.select_related("ung_vien").filter(ung_vien=user)
		
		# Nhà tuyển dụng xem được tất cả hồ sơ ứng viên
		if user.vai_tro == NguoiDung.VaiTro.CONG_TY:
			return HoSoUngVien.objects.select_related("ung_vien").all()
		
		return HoSoUngVien.objects.select_related("ung_vien").none()

	def get_permissions(self):
		"""
		Xác định quyền theo action:
		- retrieve: IsEmployerOrCandidateSelf (xem được hồ sơ của mình hoặc là nhà tuyển dụng)
		- update, partial_update, destroy: IsCandidateSelf (chỉ ứng viên mới được chỉnh sửa hồ sơ của mình)
		- create, list: IsAuthenticated
		"""
		if self.action in ["retrieve"]:
			self.permission_classes = [IsAuthenticated, IsEmployerOrCandidateSelf]
		elif self.action in ["update", "partial_update", "destroy", "me", "download_cv"]:
			self.permission_classes = [IsAuthenticated, IsCandidateSelf]
		elif self.action in ["upload_avatar"]:
			self.permission_classes = [IsAuthenticated]
		else:
			self.permission_classes = [IsAuthenticated]
		
		return super().get_permissions()

	def perform_create(self, serializer):
		if self.request.user.vai_tro != NguoiDung.VaiTro.UNG_VIEN:
			raise serializers.ValidationError({"detail": "Chỉ ứng viên mới có thể tạo hồ sơ ứng viên."})
		if HoSoUngVien.objects.filter(ung_vien=self.request.user).exists():
			raise serializers.ValidationError({"detail": "Hồ sơ ứng viên đã tồn tại."})
		serializer.save(ung_vien=self.request.user)

	@extend_schema(
		summary='Update my candidate profile partially',
		description='Candidate updates own profile without sending ung_vien id in path.',
		tags=['profiles'],
		request=HoSoUngVienSerializer,
		responses={200: HoSoUngVienSerializer},
	)
	@action(detail=False, methods=["patch"], url_path="me")
	def me(self, request):
		if request.user.vai_tro != NguoiDung.VaiTro.UNG_VIEN:
			raise PermissionDenied("Chỉ ứng viên mới có thể chỉnh sửa hồ sơ của chính mình.")

		try:
			profile = HoSoUngVien.objects.select_related("ung_vien").get(ung_vien=request.user)
		except HoSoUngVien.DoesNotExist as exc:
			raise NotFound("Không tìm thấy hồ sơ ứng viên của bạn.") from exc

		self.check_object_permissions(request, profile)
		serializer = self.get_serializer(profile, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_200_OK)

	@extend_schema(
		summary='Upload candidate avatar image',
		description='Upload ảnh đại diện và nhận URL ảnh để PATCH vào hồ sơ ứng viên.',
		tags=['profiles'],
		request=AvatarUploadRequestSerializer,
		responses={200: OpenApiResponse(description='Avatar uploaded successfully')},
	)
	@action(
		detail=False,
		methods=["post"],
		url_path="upload-avatar",
		parser_classes=[MultiPartParser, FormParser],
	)
	def upload_avatar(self, request):
		if request.user.vai_tro != NguoiDung.VaiTro.UNG_VIEN:
			raise PermissionDenied("Chỉ ứng viên mới có thể tải ảnh đại diện.")

		try:
			profile = HoSoUngVien.objects.select_related("ung_vien").get(ung_vien=request.user)
		except HoSoUngVien.DoesNotExist as exc:
			raise NotFound("Không tìm thấy hồ sơ ứng viên của bạn.") from exc

		serializer = AvatarUploadRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		uploaded_file = serializer.validated_data["file"]

		if uploaded_file.size > MAX_AVATAR_SIZE:
			raise serializers.ValidationError({"file": "Kích thước ảnh tối đa là 2MB."})

		if not str(uploaded_file.content_type or "").startswith("image/"):
			raise serializers.ValidationError({"file": "Chỉ cho phép tải lên file ảnh."})

		file_extension = Path(uploaded_file.name).suffix.lower()
		if file_extension not in ALLOWED_AVATAR_EXTENSIONS:
			raise serializers.ValidationError(
				{"file": "Định dạng ảnh không hợp lệ. Chỉ hỗ trợ jpg, jpeg, png, webp, gif."}
			)

		safe_file_name = f"avatars/candidate_{request.user.id}_{uuid4().hex}{file_extension}"
		saved_path = default_storage.save(safe_file_name, uploaded_file)
		avatar_url = request.build_absolute_uri(default_storage.url(saved_path))

		profile.avatar = avatar_url
		profile.save(update_fields=["avatar", "updated_at"])

		return Response({"avatar_url": avatar_url}, status=status.HTTP_200_OK)

	@extend_schema(
		summary='Download candidate CV as PDF',
		description='Download candidate profile as PDF file. Only candidate can download their own CV. Supports multiple templates and export formats (Phase 2).',
		tags=['profiles'],
		parameters=[
			{
				'name': 'template',
				'in': 'query',
				'description': 'CV template style: professional (default), modern, minimal',
				'schema': {'type': 'string', 'enum': ['professional', 'modern', 'minimal']},
			},
		],
		responses={200: OpenApiResponse(description='PDF file download')},
	)
	@action(detail=False, methods=["get"], url_path="download-cv")
	def download_cv(self, request):
		"""Download candidate CV as PDF with optional template selection."""
		if request.user.vai_tro != NguoiDung.VaiTro.UNG_VIEN:
			raise PermissionDenied("Chỉ ứng viên mới có thể tải CV.")

		try:
			profile = HoSoUngVien.objects.select_related("ung_vien").get(ung_vien=request.user)
		except HoSoUngVien.DoesNotExist as exc:
			raise NotFound("Không tìm thấy hồ sơ ứng viên của bạn.") from exc

		try:
			# Phase 2: Support template selection
			template_name = request.query_params.get('template', 'professional')
			template_class = get_template_class(template_name)
			
			# Generate PDF using selected template
			filename = f"CV_{profile.ho_ten or 'CV'}_{datetime.now().strftime('%d%m%Y')}.pdf"
			generator = template_class(profile, filename)
			pdf_buffer = generator.generate()
			
			response = FileResponse(pdf_buffer, content_type='application/pdf')
			response['Content-Disposition'] = f'attachment; filename="{filename}"'
			return response
		except Exception as e:
			return Response(
				{"detail": f"Lỗi tạo CV: {str(e)}"},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)


@extend_schema_view(
	list=extend_schema(
		summary='List company profiles',
		tags=['profiles'],
		responses={200: HoSoCongTySerializer(many=True)},
	),
	retrieve=extend_schema(
		summary='Get company profile',
		tags=['profiles'],
		responses={200: HoSoCongTySerializer},
	),
	create=extend_schema(
		summary='Create company profile',
		tags=['profiles'],
		request=HoSoCongTySerializer,
		responses={201: HoSoCongTySerializer},
		examples=[
			OpenApiExample(
				'name',
				value={
					'cong_ty': 2,
					'ten_cong_ty': 'ABC Tech',
					'linh_vuc': 'Software',
					'lich_su': 'Outsourcing and product development',
					'lien_he': 'hr@abctech.com',
					'dia_chi': 'HCM',
				},
				request_only=True,
			),
		],
	),
	update=extend_schema(
		summary='Replace company profile',
		tags=['profiles'],
		request=HoSoCongTySerializer,
		responses={200: HoSoCongTySerializer},
	),
	partial_update=extend_schema(
		summary='Update company profile partially',
		tags=['profiles'],
		request=HoSoCongTySerializer,
		responses={200: HoSoCongTySerializer},
	),
	destroy=extend_schema(
		summary='Delete company profile',
		tags=['profiles'],
		responses={204: OpenApiResponse(description='Company profile deleted')},
	),
)
class HoSoCongTyViewSet(viewsets.ModelViewSet):
	queryset = HoSoCongTy.objects.all()
	serializer_class = HoSoCongTySerializer

	def get_queryset(self):
		user = self.request.user
		if user.is_superuser:
			return HoSoCongTy.objects.all()
		return HoSoCongTy.objects.filter(cong_ty=user)

	def perform_create(self, serializer):
		if self.request.user.vai_tro != NguoiDung.VaiTro.CONG_TY:
			raise serializers.ValidationError({"detail": "Chỉ công ty mới có thể tạo hồ sơ công ty."})
		if HoSoCongTy.objects.filter(cong_ty=self.request.user).exists():
			raise serializers.ValidationError({"detail": "Hồ sơ công ty đã tồn tại."})
		serializer.save(cong_ty=self.request.user)
