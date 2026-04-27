from django.urls import path
from rest_framework.routers import DefaultRouter
from modules.candidate_matching.views import (
    JobMatchingViewSet,
    JobPersonalityRequirementViewSet,
    CandidatePersonalityProfileViewSet,
)

router = DefaultRouter()
router.register(r'personality-requirements', JobPersonalityRequirementViewSet, basename='personality-requirement')
router.register(r'candidate-profiles', CandidatePersonalityProfileViewSet, basename='candidate-profile')

urlpatterns = [
    path('jobs/<int:job_id>/candidates/', JobMatchingViewSet.as_view({'get': 'find_candidates_for_job'}), name='job-candidates'),
    path('jobs/<int:job_id>/eligible-candidates/', JobMatchingViewSet.as_view({'get': 'get_eligible_candidates'}), name='eligible-candidates'),
] + router.urls
