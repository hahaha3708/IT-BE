from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Health check',
        description='Lightweight endpoint used to verify that the backend is running.',
        tags=['system'],
        responses={200: OpenApiResponse(response=inline_serializer(name='HealthCheckResponse', fields={'status': serializers.CharField()}))},
        auth=[],
    )
    def get(self, request):
        return Response({"status": "ok"})
