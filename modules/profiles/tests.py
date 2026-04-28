from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

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
		user = NguoiDung.objects.get(email=email)
		self.client.force_authenticate(user=user)

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

	def test_candidate_can_patch_own_profile(self):
		profile = HoSoUngVien.objects.create(ung_vien=self.candidate, ho_ten="Original Name")

		self._authenticate("candidate-profile@example.com", "Secret123!")
		response = self.client.patch(
			f"/api/profiles/candidate/{profile.ung_vien_id}/",
			{
				"ho_ten": "Updated Name",
				"location": "Ho Chi Minh",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		profile.refresh_from_db()
		self.assertEqual(profile.ho_ten, "Updated Name")
		self.assertEqual(profile.location, "Ho Chi Minh")

	def test_candidate_cannot_patch_other_candidate_profile(self):
		other_candidate = NguoiDung.objects.create_user(
			email="candidate-edit-other@example.com",
			password="Secret123!",
			vai_tro=NguoiDung.VaiTro.UNG_VIEN,
		)
		other_profile = HoSoUngVien.objects.create(ung_vien=other_candidate, ho_ten="Other Candidate")

		self._authenticate("candidate-profile@example.com", "Secret123!")
		response = self.client.patch(
			f"/api/profiles/candidate/{other_profile.ung_vien_id}/",
			{"ho_ten": "Hacked Name"},
			format="json",
		)

		# Candidate queryset chỉ chứa hồ sơ của chính user nên trường hợp này trả về 404.
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_company_cannot_patch_candidate_profile(self):
		profile = HoSoUngVien.objects.create(ung_vien=self.candidate, ho_ten="Candidate Name")

		self._authenticate("company-profile@example.com", "Secret123!")
		response = self.client.patch(
			f"/api/profiles/candidate/{profile.ung_vien_id}/",
			{"ho_ten": "Company Updated"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_candidate_can_patch_own_profile_via_me_endpoint(self):
		profile = HoSoUngVien.objects.create(ung_vien=self.candidate, ho_ten="Original Name")

		self._authenticate("candidate-profile@example.com", "Secret123!")
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			{
				"ho_ten": "Updated Via Me",
				"location": "Da Nang",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		profile.refresh_from_db()
		self.assertEqual(profile.ho_ten, "Updated Via Me")
		self.assertEqual(profile.location, "Da Nang")

	def test_company_cannot_patch_profile_via_me_endpoint(self):
		self._authenticate("company-profile@example.com", "Secret123!")
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			{"ho_ten": "Should Fail"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_candidate_me_endpoint_returns_404_when_profile_not_found(self):
		self._authenticate("candidate-profile@example.com", "Secret123!")
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			{"ho_ten": "No Profile"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_unauthenticated_user_cannot_patch_profile_via_me_endpoint(self):
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			{"ho_ten": "Unauthorized"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_candidate_cannot_change_profile_owner_via_me_endpoint(self):
		other_candidate = NguoiDung.objects.create_user(
			email="candidate-owner-tamper@example.com",
			password="Secret123!",
			vai_tro=NguoiDung.VaiTro.UNG_VIEN,
		)
		profile = HoSoUngVien.objects.create(ung_vien=self.candidate, ho_ten="Owner Locked")

		self._authenticate("candidate-profile@example.com", "Secret123!")
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			{
				"ung_vien": other_candidate.id,
				"ho_ten": "Still Mine",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		profile.refresh_from_db()
		self.assertEqual(profile.ung_vien_id, self.candidate.id)


# ===== PHASE 2 TESTS: Kiểm thử các trường mới (hoc_van, chung_chi, ngoai_ngu, du_an, gioi_thieu) =====
class ProfilePhase2Tests(APITestCase):
	"""Test API PATCH /api/profiles/candidate/me/ với các trường mới"""

	def setUp(self):
		self.candidate = NguoiDung.objects.create_user(
			email="phase2-candidate@example.com",
			password="Secret123!",
			vai_tro=NguoiDung.VaiTro.UNG_VIEN,
		)
		self.profile = HoSoUngVien.objects.create(
			ung_vien=self.candidate,
			ho_ten="Test Candidate",
			ky_nang="Python, Django",
		)
		self.client.force_authenticate(user=self.candidate)

	def test_patch_gioi_thieu_field(self):
		"""Test cập nhật trường giới thiệu"""
		payload = {
			"gioi_thieu": "Tôi là một lập trình viên Python có 3 năm kinh nghiệm"
		}
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			payload,
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.profile.refresh_from_db()
		self.assertEqual(self.profile.gioi_thieu, payload["gioi_thieu"])
		self.assertIn("gioi_thieu", response.data)

	def test_patch_hoc_van_field(self):
		"""Test cập nhật trường học vấn (array)"""
		payload = {
			"hoc_van": [
				{
					"truong": "Đại học Bách Khoa TP.HCM",
					"nganh": "Khoa học Máy tính",
					"nam_tot_nghiep": 2022
				},
				{
					"truong": "Đại học Quốc Phòng",
					"nganh": "Kỹ thuật Quân sự",
					"nam_tot_nghiep": 2020
				}
			]
		}
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			payload,
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.profile.refresh_from_db()
		self.assertEqual(self.profile.hoc_van, payload["hoc_van"])
		self.assertEqual(len(self.profile.hoc_van), 2)

	def test_patch_chung_chi_field(self):
		"""Test cập nhật trường chứng chỉ (array)"""
		payload = {
			"chung_chi": [
				{
					"ten_chung_chi": "AWS Solutions Architect",
					"nha_cap": "Amazon Web Services",
					"nam_cap": 2023
				},
				{
					"ten_chung_chi": "IELTS",
					"nha_cap": "British Council",
					"nam_cap": 2022,
					"diem": 7.5
				}
			]
		}
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			payload,
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.profile.refresh_from_db()
		self.assertEqual(self.profile.chung_chi, payload["chung_chi"])

	def test_patch_ngoai_ngu_field(self):
		"""Test cập nhật trường ngoại ngữ (array)"""
		payload = {
			"ngoai_ngu": [
				{
					"ten_ngoai_ngu": "Tiếng Anh",
					"tro_cap": "Advanced (B2)"
				},
				{
					"ten_ngoai_ngu": "Tiếng Nhật",
					"tro_cap": "Beginner (N4)"
				}
			]
		}
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			payload,
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.profile.refresh_from_db()
		self.assertEqual(self.profile.ngoai_ngu, payload["ngoai_ngu"])

	def test_patch_du_an_field(self):
		"""Test cập nhật trường dự án (array)"""
		payload = {
			"du_an": [
				{
					"ten_du_an": "E-commerce Platform",
					"mo_ta": "Xây dựng nền tảng thương mại điện tử sử dụng Django",
					"cong_nghe": "Django, PostgreSQL, React",
					"link": "https://github.com/username/ecommerce"
				},
				{
					"ten_du_an": "AI Chatbot",
					"mo_ta": "Chatbot hỗ trợ khách hàng sử dụng NLP",
					"cong_nghe": "Python, NLP, Flask",
					"link": "https://github.com/username/chatbot"
				}
			]
		}
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			payload,
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.profile.refresh_from_db()
		self.assertEqual(self.profile.du_an, payload["du_an"])
		self.assertEqual(len(self.profile.du_an), 2)

	def test_patch_all_new_fields_together(self):
		"""Test cập nhật tất cả trường mới cùng một lúc"""
		payload = {
			"gioi_thieu": "Lập trình viên Full Stack có 5 năm kinh nghiệm",
			"hoc_van": [
				{
					"truong": "Đại học Công Nghệ",
					"nganh": "Khoa học Máy tính",
					"nam_tot_nghiep": 2022
				}
			],
			"chung_chi": [
				{
					"ten_chung_chi": "AWS Certified",
					"nha_cap": "Amazon",
					"nam_cap": 2023
				}
			],
			"ngoai_ngu": [
				{
					"ten_ngoai_ngu": "Tiếng Anh",
					"tro_cap": "Advanced"
				}
			],
			"du_an": [
				{
					"ten_du_an": "Project X",
					"mo_ta": "Dự án thương mại điện tử",
					"cong_nghe": "Django, React",
					"link": "https://github.com/user/projectx"
				}
			]
		}
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			payload,
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.profile.refresh_from_db()
		self.assertEqual(self.profile.gioi_thieu, payload["gioi_thieu"])
		self.assertEqual(len(self.profile.hoc_van), 1)
		self.assertEqual(len(self.profile.chung_chi), 1)
		self.assertEqual(len(self.profile.ngoai_ngu), 1)
		self.assertEqual(len(self.profile.du_an), 1)

	def test_patch_partial_update_preserves_existing_data(self):
		"""Test cập nhật một phần không ảnh hưởng đến dữ liệu cũ"""
		# Set giá trị ban đầu
		self.profile.gioi_thieu = "Giới thiệu cũ"
		self.profile.hoc_van = [{"truong": "Đại học A", "nganh": "CNTT", "nam_tot_nghiep": 2020}]
		self.profile.save()

		# Cập nhật chỉ chứng chỉ
		payload = {
			"chung_chi": [
				{"ten_chung_chi": "AWS", "nha_cap": "Amazon", "nam_cap": 2023}
			]
		}
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			payload,
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.profile.refresh_from_db()

		# Kiểm tra giá trị cũ vẫn được giữ
		self.assertEqual(self.profile.gioi_thieu, "Giới thiệu cũ")
		self.assertEqual(len(self.profile.hoc_van), 1)
		self.assertEqual(self.profile.hoc_van[0]["truong"], "Đại học A")

		# Kiểm tra giá trị mới
		self.assertEqual(len(self.profile.chung_chi), 1)
		self.assertEqual(self.profile.chung_chi[0]["ten_chung_chi"], "AWS")

	def test_patch_empty_array_fields(self):
		"""Test cập nhật các trường thành mảng rỗng"""
		self.profile.hoc_van = [{"truong": "University", "nganh": "CS", "nam_tot_nghiep": 2020}]
		self.profile.save()

		payload = {
			"hoc_van": [],
			"chung_chi": [],
			"ngoai_ngu": [],
			"du_an": []
		}
		response = self.client.patch(
			"/api/profiles/candidate/me/",
			payload,
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.profile.refresh_from_db()
		self.assertEqual(self.profile.hoc_van, [])
		self.assertEqual(self.profile.chung_chi, [])
		self.assertEqual(self.profile.ngoai_ngu, [])
		self.assertEqual(self.profile.du_an, [])

	def test_get_profile_includes_new_fields(self):
		"""Test GET /api/profiles/candidate/<id>/ trả về các trường mới"""
		self.profile.gioi_thieu = "Giới thiệu test"
		self.profile.hoc_van = [{"truong": "University", "nganh": "CS", "nam_tot_nghiep": 2020}]
		self.profile.chung_chi = [{"ten_chung_chi": "AWS", "nha_cap": "Amazon", "nam_cap": 2023}]
		self.profile.ngoai_ngu = [{"ten_ngoai_ngu": "Tiếng Anh", "tro_cap": "Advanced"}]
		self.profile.du_an = [{"ten_du_an": "Project X", "mo_ta": "Test project", "cong_nghe": "Python"}]
		self.profile.save()

		response = self.client.get(f"/api/profiles/candidate/{self.profile.ung_vien_id}/", format="json")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("gioi_thieu", response.data)
		self.assertIn("hoc_van", response.data)
		self.assertIn("chung_chi", response.data)
		self.assertIn("ngoai_ngu", response.data)
		self.assertIn("du_an", response.data)
		self.assertEqual(response.data["gioi_thieu"], "Giới thiệu test")
		self.assertEqual(len(response.data["hoc_van"]), 1)


class AvatarUploadTests(APITestCase):
	def setUp(self):
		self.candidate = NguoiDung.objects.create_user(
			email="avatar-candidate@example.com",
			password="Secret123!",
			vai_tro=NguoiDung.VaiTro.UNG_VIEN,
		)
		self.company = NguoiDung.objects.create_user(
			email="avatar-company@example.com",
			password="Secret123!",
			vai_tro=NguoiDung.VaiTro.CONG_TY,
		)
		self.profile = HoSoUngVien.objects.create(ung_vien=self.candidate, ho_ten="Avatar Candidate")

	def test_candidate_can_upload_avatar(self):
		self.client.force_authenticate(user=self.candidate)
		image = SimpleUploadedFile("avatar.png", b"fake-image-bytes", content_type="image/png")

		response = self.client.post(
			"/api/profiles/candidate/upload-avatar/",
			{"file": image},
			format="multipart",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("avatar_url", response.data)
		self.profile.refresh_from_db()
		self.assertEqual(self.profile.avatar, response.data["avatar_url"])

	def test_company_cannot_upload_candidate_avatar(self):
		self.client.force_authenticate(user=self.company)
		image = SimpleUploadedFile("avatar.png", b"fake-image-bytes", content_type="image/png")

		response = self.client.post(
			"/api/profiles/candidate/upload-avatar/",
			{"file": image},
			format="multipart",
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_upload_avatar_rejects_non_image_file(self):
		self.client.force_authenticate(user=self.candidate)
		non_image = SimpleUploadedFile("note.txt", b"hello world", content_type="text/plain")

		response = self.client.post(
			"/api/profiles/candidate/upload-avatar/",
			{"file": non_image},
			format="multipart",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("file", response.data)
