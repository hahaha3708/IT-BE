from rest_framework import serializers, viewsets
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view

from modules.accounts.models import NguoiDung
from modules.profiles.models import HoSoCongTy, HoSoUngVien
from modules.profiles.serializers import HoSoCongTySerializer, HoSoUngVienSerializer


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

	def get_queryset(self):
		user = self.request.user
		if user.is_superuser:
			return HoSoUngVien.objects.all()
		return HoSoUngVien.objects.filter(ung_vien=user)

	def perform_create(self, serializer):
		if self.request.user.vai_tro != NguoiDung.VaiTro.UNG_VIEN:
			raise serializers.ValidationError({"detail": "Chỉ ứng viên mới có thể tạo hồ sơ ứng viên."})
		if HoSoUngVien.objects.filter(ung_vien=self.request.user).exists():
			raise serializers.ValidationError({"detail": "Hồ sơ ứng viên đã tồn tại."})
		serializer.save(ung_vien=self.request.user)


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
