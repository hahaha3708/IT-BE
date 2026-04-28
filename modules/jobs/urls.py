from django.urls import path
from rest_framework.routers import DefaultRouter

from modules.jobs.views import TinTuyenDungViewSet

router = DefaultRouter()
router.register(r"posts", TinTuyenDungViewSet, basename="job-posts")

urlpatterns = [
] + router.urls
