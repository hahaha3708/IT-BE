from rest_framework import status
from rest_framework.test import APITestCase

from modules.accounts.models import NguoiDung
from modules.profiles.models import HoSoCongTy, HoSoUngVien


class ProfileOwnershipTests(APITestCase):
	def setUp(self):
		self.candidate = NguoiDung.objects.create_user(
			email="candidate-profile@example.com",
			password="Secret123!",
			vai_tro=NguoiDung.VaiTro.UNG_VIEN,
		)
		self.company = NguoiDung.objects.create_user(
			email="company-profile@example.com",
			password="Secret123!",
			vai_tro=NguoiDung.VaiTro.CONG_TY,
		)

	def _authenticate(self, email, password):
		response = self.client.post(
			"/api/auth/login/",
			{"email": email, "password": password},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

	def test_candidate_can_create_own_profile_without_user_id(self):
		self._authenticate("candidate-profile@example.com", "Secret123!")

		response = self.client.post(
			"/api/profiles/candidate/",
			{
				"ho_ten": "Nguyen Van A",
				"so_dien_thoai": "0900000000",
				"location": "Da Nang",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(HoSoUngVien.objects.filter(ung_vien=self.candidate).exists())

	def test_company_cannot_create_candidate_profile(self):
		self._authenticate("company-profile@example.com", "Secret123!")

		response = self.client.post(
			"/api/profiles/candidate/",
			{
				"ho_ten": "Wrong Role",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_company_can_create_own_profile_without_user_id(self):
		self._authenticate("company-profile@example.com", "Secret123!")

		response = self.client.post(
			"/api/profiles/company/",
			{
				"ten_cong_ty": "TalentFlow Global JSC",
				"linh_vuc": "Cong nghe thong tin",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(HoSoCongTy.objects.filter(cong_ty=self.company).exists())

	def test_candidate_list_only_returns_self_profile(self):
		other_candidate = NguoiDung.objects.create_user(
			email="candidate-other@example.com",
			password="Secret123!",
			vai_tro=NguoiDung.VaiTro.UNG_VIEN,
		)
		HoSoUngVien.objects.create(ung_vien=self.candidate, ho_ten="Self")
		HoSoUngVien.objects.create(ung_vien=other_candidate, ho_ten="Other")

		self._authenticate("candidate-profile@example.com", "Secret123!")
		response = self.client.get("/api/profiles/candidate/", format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["ho_ten"], "Self")
