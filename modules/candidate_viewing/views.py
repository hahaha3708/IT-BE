from django.shortcuts import get_object_or_404
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema

from modules.candidate_viewing.pagination import CandidatePagination
from modules.candidate_viewing.permissions import IsEmployer
from modules.candidate_viewing.serializers import (
	CandidateDetailSerializer,
	CandidateEvaluationSerializer,
	CandidateListItemSerializer,
)
from modules.candidate_viewing.services import (
	apply_candidate_filters,
	calculate_matching_score,
	candidate_has_availability_overlap,
	build_review_summary,
	filter_candidates_by_slots,
	parse_search_params,
	sort_candidates,
)
from modules.jobs.models import TinTuyenDung
from modules.profiles.models import HoSoUngVien
from modules.reviews.models import DanhGia


class BaseCandidateSearchAPIView(APIView):
	permission_classes = [permissions.IsAuthenticated, IsEmployer]
	pagination_class = CandidatePagination
	serializer_class = CandidateListItemSerializer

	def get_search_params(self):
		return parse_search_params(self.request.query_params)

	def get_target_job(self):
		return None

	def get_queryset(self, params):
		queryset = HoSoUngVien.objects.all()
		queryset = apply_candidate_filters(queryset, params)
		return queryset

	def build_response(self, queryset, params, job=None):
		candidates = list(queryset)
		candidates = filter_candidates_by_slots(candidates, params.availability_slots)

		scored_candidates = []
		for candidate in candidates:
			if job is None and params.availability_slots and not candidate_has_availability_overlap(candidate, params.availability_slots):
				continue
			candidate._matching_score = calculate_matching_score(candidate, params, job=job)
			scored_candidates.append((candidate, candidate._matching_score))

		ordered_candidates = sort_candidates(scored_candidates, params)
		ordered_items = [candidate for candidate, _score in ordered_candidates]
		paginated_payload = self.pagination_class().paginate(ordered_items, self.request.query_params)
		paginated_payload["results"] = self.serializer_class(
			paginated_payload["results"],
			many=True,
			context={"request": self.request},
		).data
		return Response(paginated_payload)


class CandidatePaginationResponseSerializer(serializers.Serializer):
	page = serializers.IntegerField()
	limit = serializers.IntegerField()
	total = serializers.IntegerField()
	results = CandidateListItemSerializer(many=True)


candidate_search_parameters = [
	OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description='1-based page number'),
	OpenApiParameter(name='limit', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description='Page size up to 100'),
	OpenApiParameter(name='sort', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='Sort order. Allowed values: matching_desc, updated_desc.'),
	OpenApiParameter(name='q', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='Search by candidate name or skills'),
	OpenApiParameter(name='location', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='Location filter'),
	OpenApiParameter(name='salary_min', type=OpenApiTypes.NUMBER, location=OpenApiParameter.QUERY, required=False, description='Minimum expected salary'),
	OpenApiParameter(name='salary_max', type=OpenApiTypes.NUMBER, location=OpenApiParameter.QUERY, required=False, description='Maximum expected salary'),
	OpenApiParameter(name='availability_slots', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='JSON array string of availability slots'),
]


class CandidateListAPIView(BaseCandidateSearchAPIView):
	@extend_schema(
		summary='List candidates',
		description='Return employer-visible candidates with search, filter, sort and pagination support.',
		tags=['candidate-viewing'],
		parameters=candidate_search_parameters,
		responses={200: CandidatePaginationResponseSerializer},
	)
	def get(self, request):
		params = self.get_search_params()
		queryset = self.get_queryset(params)
		return self.build_response(queryset, params)


class MatchedCandidateListAPIView(BaseCandidateSearchAPIView):
	@extend_schema(
		summary='List matched candidates for a job',
		description='Return candidates scored against a specific job posting. Employer role required.',
		tags=['candidate-viewing'],
		parameters=[
			OpenApiParameter(name='job_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description='Job posting ID'),
			*candidate_search_parameters,
		],
		responses={200: CandidatePaginationResponseSerializer, 404: OpenApiResponse(description='Job not found')},
	)
	def get(self, request, job_id):
		params = self.get_search_params()
		job = get_object_or_404(TinTuyenDung, pk=job_id)
		queryset = self.get_queryset(params)
		return self.build_response(queryset, params, job=job)


class CandidateDetailAPIView(APIView):
	permission_classes = [permissions.IsAuthenticated, IsEmployer]

	@extend_schema(
		summary='Get candidate detail',
		description='Return a candidate profile with reviews and summary information. Employer role required.',
		tags=['candidate-viewing'],
		parameters=[
			OpenApiParameter(name='candidate_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description='Candidate profile ID'),
		],
		responses={200: CandidateDetailSerializer, 404: OpenApiResponse(description='Candidate not found')},
	)
	def get(self, request, candidate_id):
		candidate = get_object_or_404(HoSoUngVien, pk=candidate_id)
		reviews = list(
			DanhGia.objects.filter(nguoi_nhan_danh_gia=candidate.ung_vien)
			.order_by("-tao_luc")
			.select_related("nguoi_danh_gia")
		)
		review_summary = build_review_summary(reviews)
		serializer = CandidateDetailSerializer(
			candidate,
			context={
				"request": request,
				"reviews": reviews,
				"review_summary": review_summary,
			},
		)
		return Response(serializer.data)


class CandidateEvaluationAPIView(APIView):
	permission_classes = [permissions.IsAuthenticated, IsEmployer]

	@extend_schema(
		summary='Get candidate evaluation',
		description='Return current application status and employer review for a candidate. Employer role required.',
		tags=['candidate-viewing'],
		parameters=[
			OpenApiParameter(name='candidate_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description='Candidate profile ID'),
		],
	)
	def get(self, request, candidate_id):
		candidate = get_object_or_404(HoSoUngVien, pk=candidate_id)
		from modules.applications.models import UngTuyen
		application = UngTuyen.objects.filter(ung_vien=candidate).order_by("-thoi_gian_ung_tuyen").first()
		
		review = None
		if application:
			review = DanhGia.objects.filter(ung_tuyen=application, nguoi_danh_gia=request.user).first()
		
		serializer = CandidateEvaluationSerializer(
			candidate,
			context={"application": application, "review": review}
		)
		return Response(serializer.data)

	@extend_schema(
		summary='Update candidate evaluation',
		description='Update application status and create/update employer review. Employer role required.',
		tags=['candidate-viewing'],
		request=OpenApiTypes.OBJECT,
		responses={200: OpenApiTypes.OBJECT, 400: OpenApiResponse(description='Invalid data')},
	)
	def post(self, request, candidate_id):
		candidate = get_object_or_404(HoSoUngVien, pk=candidate_id)
		from modules.applications.models import UngTuyen
		application = UngTuyen.objects.filter(ung_vien=candidate).order_by("-thoi_gian_ung_tuyen").first()
		
		if not application:
			return Response({"detail": "Ứng viên chưa có đơn ứng tuyển nào."}, status=400)
			
		status = request.data.get("status")
		rating = request.data.get("rating")
		comment = request.data.get("comment")
		
		if status:
			application.trang_thai = status
			application.save()
			
		if rating is not None:
			DanhGia.objects.update_or_create(
				ung_tuyen=application,
				nguoi_danh_gia=request.user,
				defaults={
					"nguoi_nhan_danh_gia": candidate.ung_vien,
					"diem_so": rating,
					"nhan_xet": comment
				}
			)
			
		return Response({"message": "Cập nhật đánh giá thành công."})
