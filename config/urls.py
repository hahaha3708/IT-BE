"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from core.views import HealthCheckView
from modules.accounts.views import (
    LogoutView,
    MeView,
    NguoiDungViewSet,
    TestTokenView,
    TokenObtainPairSwaggerView,
    TokenRefreshSwaggerView,
)


register_view = NguoiDungViewSet.as_view({'post': 'create'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/auth/register/', register_view, name='auth-register'),
    path('api/auth/login/', TokenObtainPairSwaggerView.as_view(), name='auth-login'),
    path('api/auth/me/', MeView.as_view(), name='auth-me'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('api/auth/token/', TokenObtainPairSwaggerView.as_view(), name='token-obtain-pair'),
    path('api/auth/token/refresh/', TokenRefreshSwaggerView.as_view(), name='token-refresh'),
    path('api/auth/test-token/', TestTokenView.as_view(), name='test-token'),
    path('api/accounts/', include('modules.accounts.urls')),
    path('api/profiles/', include('modules.profiles.urls')),
    path('api/jobs/', include('modules.jobs.urls')),
    path('api/v1/', include('modules.candidate_viewing.urls')),
    path('api/v1/chats/', include('modules.chats.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
