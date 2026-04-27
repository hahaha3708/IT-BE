from django.test import override_settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from modules.accounts.models import NguoiDung


@override_settings(
	TEST_TOKEN_ENDPOINT_ENABLED=True,
	TEST_TOKEN_EMAIL="sprint-test@example.com",
	TEST_TOKEN_ROLE="cong_ty",
	TEST_TOKEN_PASSWORD="token-password",
	TEST_TOKEN_SHARED_SECRET="sprint-secret",
)
class TestTokenEndpointTests(APITestCase):
	def test_requires_shared_secret_when_configured(self):
		response = self.client.post("/api/auth/test-token/", format="json")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_returns_access_and_refresh_tokens(self):
		response = self.client.post(
			"/api/auth/test-token/",
			format="json",
			HTTP_X_TEST_TOKEN_SECRET="sprint-secret",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("access", response.data)
		self.assertIn("refresh", response.data)
		self.assertEqual(response.data["token_type"], "Bearer")
		self.assertEqual(response.data["user"]["email"], "sprint-test@example.com")

		user = NguoiDung.objects.get(email="sprint-test@example.com")
		self.assertEqual(response.data["user"]["id"], user.id)

	def test_generated_access_token_can_call_protected_endpoint(self):
		token_response = self.client.post(
			"/api/auth/test-token/",
			format="json",
			HTTP_X_TEST_TOKEN_SECRET="sprint-secret",
		)
		access = token_response.data["access"]

		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
		protected_response = self.client.get("/api/accounts/users/")
		self.assertEqual(protected_response.status_code, status.HTTP_200_OK)

	def test_accepts_role_from_request(self):
		response = self.client.post(
			"/api/auth/test-token/",
			{"vai_tro": "ung_vien"},
			format="json",
			HTTP_X_TEST_TOKEN_SECRET="sprint-secret",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["user"]["vai_tro"], "ung_vien")

		user = NguoiDung.objects.get(email="sprint-test@example.com")
		self.assertEqual(user.vai_tro, "ung_vien")

	def test_rejects_invalid_role(self):
		response = self.client.post(
			"/api/auth/test-token/",
			{"role": "invalid-role"},
			format="json",
			HTTP_X_TEST_TOKEN_SECRET="sprint-secret",
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("allowed_roles", response.data)


@override_settings(TEST_TOKEN_ENDPOINT_ENABLED=False)
class TestTokenEndpointDisabledTests(APITestCase):
	def test_returns_not_found_when_disabled(self):
		response = self.client.post("/api/auth/test-token/", format="json")
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AuthRoutingAliasTests(APITestCase):
	def setUp(self):
		cache.clear()

	def test_register_alias_creates_user(self):
		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "alias-register@example.com",
				"password": "Secret123!",
				"vai_tro": "ung_vien",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(NguoiDung.objects.filter(email="alias-register@example.com").exists())

	def test_login_alias_returns_jwt_pair(self):
		NguoiDung.objects.create_user(
			email="alias-login@example.com",
			password="Secret123!",
			vai_tro="ung_vien",
		)

		response = self.client.post(
			"/api/auth/login/",
			{
				"email": "alias-login@example.com",
				"password": "Secret123!",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("access", response.data)
		self.assertIn("refresh", response.data)
		self.assertEqual(response.data.get("token_type"), "Bearer")

	def test_register_alias_rejects_weak_password(self):
		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "weak-password@example.com",
				"password": "123",
				"vai_tro": "ung_vien",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("password", response.data)
		self.assertFalse(NguoiDung.objects.filter(email="weak-password@example.com").exists())

	def test_register_alias_rejects_duplicate_email(self):
		NguoiDung.objects.create_user(
			email="duplicate-register@example.com",
			password="Secret123!",
			vai_tro="ung_vien",
		)

		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "duplicate-register@example.com",
				"password": "Secret123!",
				"vai_tro": "ung_vien",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("email", response.data)


class AuthSessionEndpointsTests(APITestCase):
	def setUp(self):
		cache.clear()
		self.user = NguoiDung.objects.create_user(
			email="session-user@example.com",
			password="Secret123!",
			vai_tro="ung_vien",
		)

	def _login(self):
		response = self.client.post(
			"/api/auth/login/",
			{
				"email": "session-user@example.com",
				"password": "Secret123!",
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		return response.data

	def test_me_returns_current_user(self):
		tokens = self._login()
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

		response = self.client.get("/api/auth/me/", format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["id"], self.user.id)
		self.assertEqual(response.data["email"], "session-user@example.com")
		self.assertEqual(response.data["vai_tro"], "ung_vien")
		self.assertIn("is_active", response.data)

	def test_me_requires_authentication(self):
		response = self.client.get("/api/auth/me/", format="json")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_logout_blacklists_refresh_token(self):
		tokens = self._login()
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

		logout_response = self.client.post(
			"/api/auth/logout/",
			{"refresh": tokens["refresh"]},
			format="json",
		)
		self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

		refresh_response = self.client.post(
			"/api/auth/token/refresh/",
			{"refresh": tokens["refresh"]},
			format="json",
		)
		self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthHardeningTests(APITestCase):
	def setUp(self):
		cache.clear()
		self.user = NguoiDung.objects.create_user(
			email="hardening-user@example.com",
			password="Secret123!",
			vai_tro="ung_vien",
		)

	def test_refresh_rotates_and_blacklists_old_refresh(self):
		login_response = self.client.post(
			"/api/auth/login/",
			{
				"email": "hardening-user@example.com",
				"password": "Secret123!",
			},
			format="json",
		)
		self.assertEqual(login_response.status_code, status.HTTP_200_OK)

		old_refresh = login_response.data["refresh"]
		refresh_response = self.client.post(
			"/api/auth/token/refresh/",
			{"refresh": old_refresh},
			format="json",
		)
		self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
		self.assertIn("access", refresh_response.data)
		self.assertIn("refresh", refresh_response.data)
		self.assertEqual(refresh_response.data.get("token_type"), "Bearer")

		second_refresh_response = self.client.post(
			"/api/auth/token/refresh/",
			{"refresh": old_refresh},
			format="json",
		)
		self.assertEqual(second_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthThrottlingTests(APITestCase):
	def setUp(self):
		cache.clear()
		NguoiDung.objects.create_user(
			email="throttle-user@example.com",
			password="Secret123!",
			vai_tro="ung_vien",
		)

	def test_login_is_throttled(self):
		payload = {
			"email": "throttle-user@example.com",
			"password": "Secret123!",
		}

		responses = [self.client.post("/api/auth/login/", payload, format="json") for _ in range(11)]

		for response in responses[:10]:
			self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(responses[-1].status_code, status.HTTP_429_TOO_MANY_REQUESTS)

	def test_register_is_throttled(self):
		responses = []
		for index in range(6):
			responses.append(
				self.client.post(
					"/api/auth/register/",
					{
						"email": f"throttle-register-{index}@example.com",
						"password": "Secret123!",
						"vai_tro": "ung_vien",
					},
					format="json",
				)
			)

		for response in responses[:5]:
			self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(responses[-1].status_code, status.HTTP_429_TOO_MANY_REQUESTS)


# ===== PHASE 3 TESTS: Kiểm thử luồng đăng ký với các trường hồ sơ mới =====
class RegistrationPhase3Tests(APITestCase):
	"""Test POST /api/auth/register/ với các trường hồ sơ mới (hoc_van, chung_chi, ngoai_ngu, du_an, gioi_thieu)"""

	def setUp(self):
		cache.clear()  # Clear throttle cache

	def test_register_candidate_with_basic_profile_only(self):
		"""Test đăng ký ứng viên chỉ với email/password, không truyền profile fields"""
		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "basic-register@example.com",
				"password": "Secret123!",
				"vai_tro": "ung_vien",
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		# Kiểm tra user được tạo
		user = NguoiDung.objects.get(email="basic-register@example.com")
		self.assertEqual(user.vai_tro, "ung_vien")
		
		# Kiểm tra profile được tạo tự động với giá trị mặc định
		from modules.profiles.models import HoSoUngVien
		profile = HoSoUngVien.objects.get(ung_vien=user)
		self.assertEqual(profile.hoc_van, [])
		self.assertEqual(profile.chung_chi, [])
		self.assertEqual(profile.ngoai_ngu, [])
		self.assertEqual(profile.du_an, [])
		self.assertEqual(profile.gioi_thieu, "")

	def test_register_candidate_with_gioi_thieu(self):
		"""Test đăng ký ứng viên với trường giới thiệu"""
		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "gioi-thieu-register@example.com",
				"password": "Secret123!",
				"vai_tro": "ung_vien",
				"gioi_thieu": "Tôi là lập trình viên Python với 3 năm kinh nghiệm",
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		from modules.profiles.models import HoSoUngVien
		user = NguoiDung.objects.get(email="gioi-thieu-register@example.com")
		profile = HoSoUngVien.objects.get(ung_vien=user)
		self.assertEqual(profile.gioi_thieu, "Tôi là lập trình viên Python với 3 năm kinh nghiệm")

	def test_register_candidate_with_hoc_van(self):
		"""Test đăng ký ứng viên với danh sách học vấn"""
		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "hoc-van-register@example.com",
				"password": "Secret123!",
				"vai_tro": "ung_vien",
				"hoc_van": [
					{
						"truong": "Đại học Bách Khoa TP.HCM",
						"nganh": "Khoa học Máy tính",
						"nam_tot_nghiep": 2022
					},
					{
						"truong": "Đại học Công Nghệ",
						"nganh": "Kỹ thuật Phần mềm",
						"nam_tot_nghiep": 2023
					}
				],
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		from modules.profiles.models import HoSoUngVien
		user = NguoiDung.objects.get(email="hoc-van-register@example.com")
		profile = HoSoUngVien.objects.get(ung_vien=user)
		self.assertEqual(len(profile.hoc_van), 2)
		self.assertEqual(profile.hoc_van[0]["truong"], "Đại học Bách Khoa TP.HCM")

	def test_register_candidate_with_chung_chi(self):
		"""Test đăng ký ứng viên với danh sách chứng chỉ"""
		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "chung-chi-register@example.com",
				"password": "Secret123!",
				"vai_tro": "ung_vien",
				"chung_chi": [
					{
						"ten_chung_chi": "AWS Solutions Architect",
						"nha_cap": "Amazon Web Services",
						"nam_cap": 2023
					}
				],
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		from modules.profiles.models import HoSoUngVien
		user = NguoiDung.objects.get(email="chung-chi-register@example.com")
		profile = HoSoUngVien.objects.get(ung_vien=user)
		self.assertEqual(len(profile.chung_chi), 1)
		self.assertEqual(profile.chung_chi[0]["ten_chung_chi"], "AWS Solutions Architect")

	def test_register_candidate_with_ngoai_ngu(self):
		"""Test đăng ký ứng viên với danh sách ngoại ngữ"""
		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "ngoai-ngu-register@example.com",
				"password": "Secret123!",
				"vai_tro": "ung_vien",
				"ngoai_ngu": [
					{
						"ten_ngoai_ngu": "Tiếng Anh",
						"tro_cap": "Advanced (B2)"
					},
					{
						"ten_ngoai_ngu": "Tiếng Nhật",
						"tro_cap": "Beginner (N4)"
					}
				],
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		from modules.profiles.models import HoSoUngVien
		user = NguoiDung.objects.get(email="ngoai-ngu-register@example.com")
		profile = HoSoUngVien.objects.get(ung_vien=user)
		self.assertEqual(len(profile.ngoai_ngu), 2)

	def test_register_candidate_with_du_an(self):
		"""Test đăng ký ứng viên với danh sách dự án"""
		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "du-an-register@example.com",
				"password": "Secret123!",
				"vai_tro": "ung_vien",
				"du_an": [
					{
						"ten_du_an": "E-commerce Platform",
						"mo_ta": "Xây dựng nền tảng bán hàng trực tuyến",
						"cong_nghe": "Django, React, PostgreSQL",
						"link": "https://github.com/user/ecommerce"
					}
				],
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		from modules.profiles.models import HoSoUngVien
		user = NguoiDung.objects.get(email="du-an-register@example.com")
		profile = HoSoUngVien.objects.get(ung_vien=user)
		self.assertEqual(len(profile.du_an), 1)
		self.assertEqual(profile.du_an[0]["ten_du_an"], "E-commerce Platform")

	def test_register_candidate_with_all_profile_fields(self):
		"""Test đăng ký ứng viên với tất cả trường hồ sơ"""
		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "full-profile-register@example.com",
				"password": "Secret123!",
				"vai_tro": "ung_vien",
				"ho_ten": "Nguyen Van A",
				"gioi_thieu": "Lập trình viên Full Stack",
				"hoc_van": [
					{"truong": "ĐHBK", "nganh": "CNTT", "nam_tot_nghiep": 2022}
				],
				"chung_chi": [
					{"ten_chung_chi": "AWS", "nha_cap": "Amazon", "nam_cap": 2023}
				],
				"ngoai_ngu": [
					{"ten_ngoai_ngu": "English", "tro_cap": "B2"}
				],
				"du_an": [
					{"ten_du_an": "Project X", "mo_ta": "Test", "cong_nghe": "Python"}
				],
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		from modules.profiles.models import HoSoUngVien
		user = NguoiDung.objects.get(email="full-profile-register@example.com")
		profile = HoSoUngVien.objects.get(ung_vien=user)
		
		# Kiểm tra tất cả trường được lưu
		self.assertEqual(profile.ho_ten, "Nguyen Van A")
		self.assertEqual(profile.gioi_thieu, "Lập trình viên Full Stack")
		self.assertEqual(len(profile.hoc_van), 1)
		self.assertEqual(len(profile.chung_chi), 1)
		self.assertEqual(len(profile.ngoai_ngu), 1)
		self.assertEqual(len(profile.du_an), 1)

	def test_register_company_ignores_profile_fields(self):
		"""Test đăng ký công ty - profile fields bị bỏ qua"""
		response = self.client.post(
			"/api/auth/register/",
			{
				"email": "company-register@example.com",
				"password": "Secret123!",
				"vai_tro": "cong_ty",
				"hoc_van": [{"truong": "Test"}],  # Should be ignored for company
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		# Company không có HoSoUngVien, nên không cần kiểm tra
		user = NguoiDung.objects.get(email="company-register@example.com")
		self.assertEqual(user.vai_tro, "cong_ty")
