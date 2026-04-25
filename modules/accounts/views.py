from django.conf import settings
from rest_framework import serializers, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import (
	OpenApiExample,
	OpenApiParameter,
	OpenApiResponse,
	OpenApiTypes,
	extend_schema,
	extend_schema_view,
)

from modules.accounts.models import NguoiDung
from modules.accounts.serializers import NguoiDungSerializer


class TokenObtainRequestSerializer(serializers.Serializer):
	email = serializers.EmailField()
	password = serializers.CharField(write_only=True)


class NguoiDungCreateRequestSerializer(serializers.Serializer):
	email = serializers.EmailField()
	password = serializers.CharField(write_only=True)
	vai_tro = serializers.ChoiceField(choices=NguoiDung.VaiTro.choices)


class TokenPairResponseSerializer(serializers.Serializer):
	access = serializers.CharField()
	refresh = serializers.CharField()
	token_type = serializers.CharField()


class TokenRefreshRequestSerializer(serializers.Serializer):
	refresh = serializers.CharField()


class TokenRefreshResponseSerializer(serializers.Serializer):
	access = serializers.CharField()
	refresh = serializers.CharField(required=False)
	token_type = serializers.CharField(required=False)


class TestTokenRequestSerializer(serializers.Serializer):
	vai_tro = serializers.ChoiceField(choices=NguoiDung.VaiTro.choices, required=False)
	role = serializers.ChoiceField(choices=NguoiDung.VaiTro.choices, required=False)


class TestTokenUserSerializer(serializers.Serializer):
	id = serializers.IntegerField()
	email = serializers.EmailField()
	vai_tro = serializers.ChoiceField(choices=NguoiDung.VaiTro.choices)


class TestTokenResponseSerializer(serializers.Serializer):
	access = serializers.CharField()
	refresh = serializers.CharField()
	token_type = serializers.CharField()
	user = TestTokenUserSerializer()


class NguoiDungPatchRequestSerializer(serializers.Serializer):
	email = serializers.EmailField(required=False)
	password = serializers.CharField(write_only=True, required=False)
	vai_tro = serializers.ChoiceField(choices=NguoiDung.VaiTro.choices, required=False)


class MeResponseSerializer(serializers.Serializer):
	id = serializers.IntegerField()
	email = serializers.EmailField()
	vai_tro = serializers.ChoiceField(choices=NguoiDung.VaiTro.choices)
	is_active = serializers.BooleanField()


class LogoutRequestSerializer(serializers.Serializer):
	refresh = serializers.CharField()


class TokenObtainPairWithTypeSerializer(TokenObtainPairSerializer):
	def validate(self, attrs):
		data = super().validate(attrs)
		data["token_type"] = "Bearer"
		return data


@extend_schema_view(
	list=extend_schema(
		summary='List users',
		description='Return users accessible to the authenticated caller.',
		tags=['accounts'],
		responses={200: NguoiDungSerializer(many=True)},
	),
	create=extend_schema(
		summary='Register user',
		description='Create a new user account. This endpoint is public.',
		tags=['accounts'],
		auth=[],
		request=NguoiDungCreateRequestSerializer,
		responses={
			201: NguoiDungSerializer,
			400: OpenApiResponse(description='Invalid registration payload or weak password'),
			409: OpenApiResponse(description='Email already exists'),
		},
		examples=[
			OpenApiExample(
				'name',
				value={'email': 'candidate@example.com', 'password': 'Secret123!', 'vai_tro': 'ung_vien'},
				request_only=True,
			),
		],
	),
	retrieve=extend_schema(
		summary='Get user',
		tags=['accounts'],
		responses={200: NguoiDungSerializer},
	),
	update=extend_schema(
		summary='Replace user',
		tags=['accounts'],
		request=NguoiDungCreateRequestSerializer,
		responses={200: NguoiDungSerializer},
	),
	partial_update=extend_schema(
		summary='Update user partially',
		tags=['accounts'],
		request=NguoiDungPatchRequestSerializer,
		responses={200: NguoiDungSerializer},
	),
	destroy=extend_schema(
		summary='Delete user',
		tags=['accounts'],
		responses={204: OpenApiResponse(description='User deleted')},
	),
)
class NguoiDungViewSet(viewsets.ModelViewSet):
	queryset = NguoiDung.objects.all().order_by("id")
	serializer_class = NguoiDungSerializer
	throttle_classes = [ScopedRateThrottle]

	def get_permissions(self):
		if self.action == "create":
			return [AllowAny()]
		return [IsAuthenticated()]

	def get_throttles(self):
		if self.action == "create":
			self.throttle_scope = "auth_register"
		return super().get_throttles()


class TokenObtainPairSwaggerView(TokenObtainPairView):
	serializer_class = TokenObtainPairWithTypeSerializer
	throttle_classes = [ScopedRateThrottle]
	throttle_scope = "auth_login"

	@extend_schema(
		summary='Obtain JWT pair',
		description='Authenticate using email and password and receive access and refresh tokens.',
		tags=['auth'],
		auth=[],
		request=TokenObtainRequestSerializer,
		responses={
			200: TokenPairResponseSerializer,
			401: OpenApiResponse(description='Invalid credentials'),
				429: OpenApiResponse(description='Too many login attempts'),
		},
		examples=[
			OpenApiExample(
				'name',
				value={'email': 'employer@example.com', 'password': 'Secret123!'},
				request_only=True,
			),
		],
	)
	def post(self, request, *args, **kwargs):
		return super().post(request, *args, **kwargs)


class TokenRefreshSwaggerView(TokenRefreshView):
	@extend_schema(
		summary='Refresh JWT access token',
		description='Exchange a valid refresh token for a new access token.',
		tags=['auth'],
		auth=[],
		request=TokenRefreshRequestSerializer,
		responses={
			200: TokenRefreshResponseSerializer,
			401: OpenApiResponse(description='Invalid or expired refresh token'),
		},
		examples=[
			OpenApiExample(
				'name',
				value={'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOi...'},
				request_only=True,
			),
		],
	)
	def post(self, request, *args, **kwargs):
		response = super().post(request, *args, **kwargs)
		if response.status_code == status.HTTP_200_OK:
			response.data["token_type"] = "Bearer"
		return response


class MeView(APIView):
	permission_classes = [IsAuthenticated]

	@extend_schema(
		summary='Get current user',
		description='Return basic profile information of the authenticated user.',
		tags=['auth'],
		responses={200: MeResponseSerializer, 401: OpenApiResponse(description='Missing or invalid token')},
	)
	def get(self, request):
		user = request.user
		return Response(
			{
				"id": user.id,
				"email": user.email,
				"vai_tro": user.vai_tro,
				"is_active": user.is_active,
			},
			status=status.HTTP_200_OK,
		)


class LogoutView(APIView):
	permission_classes = [IsAuthenticated]

	@extend_schema(
		summary='Logout user',
		description='Invalidate refresh token by adding it to the blacklist.',
		tags=['auth'],
		request=LogoutRequestSerializer,
		responses={
			200: OpenApiResponse(description='Logged out successfully'),
			400: OpenApiResponse(description='Missing refresh token'),
			401: OpenApiResponse(description='Invalid token'),
		},
	)
	def post(self, request):
		serializer = LogoutRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		refresh_token = serializer.validated_data["refresh"]
		try:
			token = RefreshToken(refresh_token)
			token.blacklist()
		except TokenError:
			return Response({"detail": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

		return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


class TestTokenView(APIView):
	permission_classes = [AllowAny]
	authentication_classes = []

	@extend_schema(
		summary='Generate a test JWT pair',
		description='Internal helper endpoint for local and integration testing. Hidden from production schema.',
		tags=['auth'],
		auth=[],
		exclude=not settings.DEBUG,
		request=TestTokenRequestSerializer,
		parameters=[
			OpenApiParameter(
				name='X-Test-Token-Secret',
				location=OpenApiParameter.HEADER,
				required=False,
				type=OpenApiTypes.STR,
				description='Optional shared secret when TEST_TOKEN_SHARED_SECRET is configured.',
			),
		],
		responses={200: TestTokenResponseSerializer},
		examples=[
			OpenApiExample(
				'name',
				value={'vai_tro': 'cong_ty'},
				request_only=True,
			),
		],
	)
	def post(self, request):
		if not settings.TEST_TOKEN_ENDPOINT_ENABLED:
			raise NotFound("Test token endpoint is disabled")

		shared_secret = settings.TEST_TOKEN_SHARED_SECRET
		if shared_secret:
			request_secret = request.headers.get("X-Test-Token-Secret", "")
			if request_secret != shared_secret:
				raise PermissionDenied("Invalid shared secret")

		requested_role = request.data.get("vai_tro") or request.data.get("role")
		allowed_roles = {choice[0] for choice in NguoiDung.VaiTro.choices}
		role = requested_role or settings.TEST_TOKEN_ROLE
		if role not in allowed_roles:
			return Response(
				{"detail": "Invalid role", "allowed_roles": sorted(allowed_roles)},
				status=status.HTTP_400_BAD_REQUEST,
			)

		user, created = NguoiDung.objects.get_or_create(
			email=settings.TEST_TOKEN_EMAIL,
			defaults={
				"vai_tro": role,
				"is_active": True,
			},
		)

		fields_to_update = []
		if created:
			user.set_password(settings.TEST_TOKEN_PASSWORD)
			fields_to_update.append("password")
		if not user.is_active:
			user.is_active = True
			fields_to_update.append("is_active")
		if user.vai_tro != role:
			user.vai_tro = role
			fields_to_update.append("vai_tro")
		if fields_to_update:
			user.save(update_fields=fields_to_update)

		refresh = RefreshToken.for_user(user)
		return Response(
			{
				"access": str(refresh.access_token),
				"refresh": str(refresh),
				"token_type": "Bearer",
				"user": {
					"id": user.id,
					"email": user.email,
					"vai_tro": user.vai_tro,
				},
			},
			status=status.HTTP_200_OK,
		)
