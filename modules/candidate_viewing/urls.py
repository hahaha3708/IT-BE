from django.urls import re_path

from modules.candidate_viewing.views import CandidateDetailAPIView, CandidateListAPIView, MatchedCandidateListAPIView

urlpatterns = [
	re_path(r"^candidates/?$", CandidateListAPIView.as_view(), name="candidate-list"),
	re_path(r"^candidates/(?P<candidate_id>\d+)/?$", CandidateDetailAPIView.as_view(), name="candidate-detail"),
	re_path(r"^jobs/(?P<job_id>\d+)/matched-candidates/?$", MatchedCandidateListAPIView.as_view(), name="matched-candidates"),
]
