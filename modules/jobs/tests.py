from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from modules.jobs.models import TinTuyenDung
from modules.profiles.models import HoSoCongTy


class TinTuyenDungViewSetTests(APITestCase):
	def setUp(self):
		self.list_url = reverse("job-posts-list")
		user_model = get_user_model()
		self.company_user = user_model.objects.create_user(
			email="company@example.com",
			password="password123",
			vai_tro=user_model.VaiTro.CONG_TY,
		)
		self.company_profile = HoSoCongTy.objects.create(
			cong_ty=self.company_user,
			ten_cong_ty="Cong Ty ABC",
			linh_vuc="Cong nghe",
			dia_chi="Da Nang",
		)

		start_time = timezone.now()
		end_time = start_time + timedelta(days=30)

		self.open_job = TinTuyenDung.objects.create(
			cong_ty=self.company_profile,
			tieu_de="Lập trình viên Python",
			noi_dung="Tuyển lập trình viên Python làm việc với Django REST API.",
			bat_dau_lam=start_time,
			ket_thuc_lam=end_time,
			luong_theo_gio=Decimal("120.00"),
			dia_diem_lam_viec="Da Nang",
			trang_thai=TinTuyenDung.TrangThai.DANG_MO,
		)
		self.closed_job = TinTuyenDung.objects.create(
			cong_ty=self.company_profile,
			tieu_de="Nhân viên hỗ trợ",
			noi_dung="Công việc hỗ trợ nội bộ cho doanh nghiệp.",
			bat_dau_lam=start_time,
			ket_thuc_lam=end_time,
			luong_theo_gio=Decimal("80.00"),
			dia_diem_lam_viec="Hue",
			trang_thai=TinTuyenDung.TrangThai.DA_DONG,
		)

	def test_list_is_public_and_returns_only_open_jobs_by_default(self):
		response = self.client.get(self.list_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["page"], 1)
		self.assertEqual(response.data["limit"], 20)
		self.assertEqual(response.data["total"], 1)
		self.assertEqual(len(response.data["results"]), 1)
		payload = response.data["results"][0]
		self.assertEqual(payload["tin_id"], self.open_job.tin_id)
		self.assertEqual(payload["trang_thai"], TinTuyenDung.TrangThai.DANG_MO)
		self.assertEqual(payload["title"], self.open_job.tieu_de)
		self.assertEqual(payload["description"], self.open_job.noi_dung)
		self.assertEqual(payload["summary"], self.open_job.noi_dung)
		self.assertEqual(payload["salary"], "120.00 / giờ")
		self.assertEqual(payload["status"], "Đang mở")
		self.assertEqual(payload["openings"], 1)
		self.assertEqual(payload["location"], self.open_job.dia_diem_lam_viec)
		self.assertIn("raw", payload)
		self.assertEqual(payload["raw"]["tin_id"], self.open_job.tin_id)
		self.assertEqual(payload["raw"]["tieu_de"], self.open_job.tieu_de)

	def test_list_can_filter_by_keyword(self):
		response = self.client.get(self.list_url, {"q": "python"})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["total"], 1)
		self.assertEqual(len(response.data["results"]), 1)
		self.assertEqual(response.data["results"][0]["tin_id"], self.open_job.tin_id)
		self.assertEqual(response.data["results"][0]["summary"], self.open_job.noi_dung)

	def test_list_can_filter_by_location(self):
		response = self.client.get(self.list_url, {"dia_diem": "da nang"})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["total"], 1)
		self.assertEqual(len(response.data["results"]), 1)
		self.assertEqual(response.data["results"][0]["tin_id"], self.open_job.tin_id)

	def test_list_can_filter_by_salary(self):
		response = self.client.get(self.list_url, {"luong_min": "100"})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["total"], 1)
		self.assertEqual(len(response.data["results"]), 1)
		self.assertEqual(response.data["results"][0]["tin_id"], self.open_job.tin_id)

	def test_list_can_filter_by_status(self):
		response = self.client.get(self.list_url, {"trang_thai": TinTuyenDung.TrangThai.DA_DONG})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["total"], 1)
		self.assertEqual(len(response.data["results"]), 1)
		self.assertEqual(response.data["results"][0]["tin_id"], self.closed_job.tin_id)

	def test_list_supports_pagination(self):
		response = self.client.get(self.list_url, {"trang_thai": TinTuyenDung.TrangThai.DANG_MO, "page": 1, "limit": 1})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["page"], 1)
		self.assertEqual(response.data["limit"], 1)
		self.assertEqual(response.data["total"], 1)
		self.assertEqual(len(response.data["results"]), 1)

	def test_list_returns_bad_request_for_invalid_page(self):
		response = self.client.get(self.list_url, {"page": "abc"})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("page", response.data)

	def test_list_returns_bad_request_for_invalid_salary(self):
		response = self.client.get(self.list_url, {"luong_min": "abc"})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("luong_min", response.data)

	def test_retrieve_job_details_includes_company_and_action_info(self):
		detail_url = reverse("job-posts-detail", args=[self.open_job.tin_id])
		self.client.force_authenticate(user=self.company_user)

		response = self.client.get(detail_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		payload = response.data
		self.assertEqual(payload["tin_id"], self.open_job.tin_id)
		self.assertEqual(payload["company_name"], self.company_profile.ten_cong_ty)
		self.assertEqual(payload["posting_title"], self.open_job.tieu_de)
		self.assertEqual(payload["job_title"], self.open_job.tieu_de)
		self.assertEqual(payload["location"], self.open_job.dia_diem_lam_viec)
		self.assertEqual(payload["job_description"], self.open_job.noi_dung)
		self.assertIsInstance(payload["edit_action"], dict)
		self.assertTrue(payload["edit_action"]["available"])
		self.assertIsInstance(payload["delete_action"], dict)
		self.assertTrue(payload["delete_action"]["available"])
