from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.candidate_viewing.pagination import CandidatePagination
from modules.candidate_viewing.permissions import IsEmployer
from modules.candidate_viewing.serializers import CandidateDetailSerializer, CandidateListItemSerializer
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


class CandidateListAPIView(BaseCandidateSearchAPIView):
	def get(self, request):
		params = self.get_search_params()
		queryset = self.get_queryset(params)
		return self.build_response(queryset, params)


class MatchedCandidateListAPIView(BaseCandidateSearchAPIView):
	def get(self, request, job_id):
		params = self.get_search_params()
		job = get_object_or_404(TinTuyenDung, pk=job_id)
		queryset = self.get_queryset(params)
		return self.build_response(queryset, params, job=job)


class CandidateDetailAPIView(APIView):
	permission_classes = [permissions.IsAuthenticated, IsEmployer]

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
