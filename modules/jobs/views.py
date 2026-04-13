from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema, extend_schema_view

from modules.jobs.models import TinTuyenDung
from modules.jobs.serializers import TinTuyenDungSerializer


@extend_schema_view(
	list=extend_schema(
		summary='List job posts',
		description='Return active job postings with optional filters.',
		tags=['jobs'],
		parameters=[
			OpenApiParameter(name='trang_thai', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='Job status filter. Allowed values: dang_mo, da_dong.'),
			OpenApiParameter(name='q', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='Keyword search across title and description'),
			OpenApiParameter(name='dia_diem', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='Location filter'),
			OpenApiParameter(name='luong_min', type=OpenApiTypes.NUMBER, location=OpenApiParameter.QUERY, required=False, description='Minimum hourly wage'),
		],
		responses={200: TinTuyenDungSerializer(many=True)},
	),
	retrieve=extend_schema(
		summary='Get job post',
		tags=['jobs'],
		responses={200: TinTuyenDungSerializer},
	),
	create=extend_schema(
		summary='Create job post',
		tags=['jobs'],
		request=TinTuyenDungSerializer,
		responses={201: TinTuyenDungSerializer},
		examples=[
			OpenApiExample(
				'name',
				value={
					'cong_ty': 1,
					'tieu_de': 'Backend Developer Part-time',
					'noi_dung': 'Build and maintain REST APIs for the matching platform.',
					'bat_dau_lam': '2026-04-20T08:00:00Z',
					'ket_thuc_lam': '2026-12-31T17:00:00Z',
					'luong_theo_gio': '20000.00',
					'dia_diem_lam_viec': 'HCM',
					'trang_thai': 'dang_mo',
				},
				request_only=True,
			),
		],
	),
	update=extend_schema(
		summary='Replace job post',
		tags=['jobs'],
		request=TinTuyenDungSerializer,
		responses={200: TinTuyenDungSerializer},
	),
	partial_update=extend_schema(
		summary='Update job post partially',
		tags=['jobs'],
		request=TinTuyenDungSerializer,
		responses={200: TinTuyenDungSerializer},
	),
	destroy=extend_schema(
		summary='Delete job post',
		tags=['jobs'],
		responses={204: OpenApiResponse(description='Job post deleted')},
	),
)
class TinTuyenDungViewSet(viewsets.ModelViewSet):
	serializer_class = TinTuyenDungSerializer
	default_queryset = TinTuyenDung.objects.select_related("cong_ty").all().order_by("-tao_luc")
	public_actions = {"list", "retrieve"}
	default_status = TinTuyenDung.TrangThai.DANG_MO
	allowed_statuses = {choice for choice, _label in TinTuyenDung.TrangThai.choices}

	def get_permissions(self):
		if self.action in self.public_actions:
			return [permissions.AllowAny()]
		return [permissions.IsAuthenticated()]

	def get_queryset(self):
		queryset = self.default_queryset
		query_params = self.request.query_params

		status = query_params.get("trang_thai", "").strip() or self.default_status
		if status not in self.allowed_statuses:
			raise ValidationError({"trang_thai": "Gia tri trang_thai khong hop le."})

		queryset = queryset.filter(trang_thai=status)

		keyword = query_params.get("q", "").strip()
		if keyword:
			queryset = queryset.filter(Q(tieu_de__icontains=keyword) | Q(noi_dung__icontains=keyword))

		location = query_params.get("dia_diem", "").strip()
		if location:
			queryset = queryset.filter(dia_diem_lam_viec__icontains=location)

		wage_min = query_params.get("luong_min", "").strip()
		if wage_min:
			try:
				minimum_salary = Decimal(wage_min)
			except InvalidOperation as exc:
				raise ValidationError({"luong_min": "luong_min phai la so hop le."}) from exc

			queryset = queryset.filter(luong_theo_gio__gte=minimum_salary)

		return queryset
