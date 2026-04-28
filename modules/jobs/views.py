from rest_framework import permissions, serializers, status, viewsets
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema, extend_schema_view

from modules.jobs.models import TinTuyenDung
from modules.jobs.pagination import JobPagination
from modules.jobs.serializers import TinTuyenDungSerializer
from modules.jobs.services import apply_job_filters


class TinTuyenDungPaginationSerializer(serializers.Serializer):
	page = serializers.IntegerField()
	limit = serializers.IntegerField()
	total = serializers.IntegerField()
	results = TinTuyenDungSerializer(many=True)


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
			OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description='1-based page number'),
			OpenApiParameter(name='limit', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description='Page size up to 100'),
		],
		responses={200: TinTuyenDungPaginationSerializer},
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
	pagination_class = JobPagination
	public_actions = {"list", "retrieve"}

	def get_permissions(self):
		if self.action in self.public_actions:
			return [permissions.AllowAny()]
		return [permissions.IsAuthenticated()]

	def get_queryset(self):
		queryset = self.default_queryset
		query_params = self.request.query_params
		queryset = apply_job_filters(queryset, query_params)
		return queryset

	def list(self, request, *args, **kwargs):
		queryset = self.filter_queryset(self.get_queryset())
		pagination_payload = self.pagination_class().paginate_queryset(queryset, request.query_params)
		pagination_payload["results"] = self.get_serializer(pagination_payload["results"], many=True).data
		return Response(pagination_payload)
