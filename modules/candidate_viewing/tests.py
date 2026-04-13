from datetime import datetime, timedelta, time as datetime_time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from modules.jobs.models import TinTuyenDung
from modules.profiles.models import HoSoCongTy, HoSoUngVien
from modules.reviews.models import DanhGia


class CandidateViewingApiTests(APITestCase):
	def setUp(self):
		user_model = get_user_model()
		self.employer_user = user_model.objects.create_user(
			email="employer@example.com",
			password="password123",
			vai_tro=user_model.VaiTro.CONG_TY,
		)
		self.candidate_user = user_model.objects.create_user(
			email="candidate@example.com",
			password="password123",
			vai_tro=user_model.VaiTro.UNG_VIEN,
		)
		self.company_profile = HoSoCongTy.objects.create(
			cong_ty=self.employer_user,
			ten_cong_ty="Cong Ty ABC",
			linh_vuc="Cong nghe",
			dia_chi="Da Nang",
		)
		self.matching_candidate = HoSoUngVien.objects.create(
			ung_vien=self.candidate_user,
			ho_ten="Nguyen Van A",
			avatar="https://cdn.example.com/candidates/a.jpg",
			so_dien_thoai="0900000001",
			ky_nang="Python, Django, REST",
			vi_tri_mong_muon="Backend Developer",
			location="Da Nang",
			availability_slots=["Mon-AM", "Tue-PM"],
			luong_mong_muon=Decimal("22000.00"),
		)
		self.other_candidate_user = user_model.objects.create_user(
			email="candidate2@example.com",
			password="password123",
			vai_tro=user_model.VaiTro.UNG_VIEN,
		)
		self.other_candidate = HoSoUngVien.objects.create(
			ung_vien=self.other_candidate_user,
			ho_ten="Tran Van B",
			ky_nang="Python, FastAPI",
			vi_tri_mong_muon="Backend Developer",
			location="Hue",
			availability_slots=["Wed-AM"],
			luong_mong_muon=Decimal("18000.00"),
		)
		self.older_candidate_user = user_model.objects.create_user(
			email="candidate3@example.com",
			password="password123",
			vai_tro=user_model.VaiTro.UNG_VIEN,
		)
		self.older_candidate = HoSoUngVien.objects.create(
			ung_vien=self.older_candidate_user,
			ho_ten="Le Van C",
			ky_nang="Java, Spring",
			vi_tri_mong_muon="Java Developer",
			location="Da Nang",
			availability_slots=["Mon-AM"],
			luong_mong_muon=Decimal("15000.00"),
		)
		older_timestamp = timezone.now() - timedelta(days=2)
		newer_timestamp = timezone.now() - timedelta(hours=1)
		HoSoUngVien.objects.filter(pk=self.matching_candidate.pk).update(updated_at=older_timestamp)
		HoSoUngVien.objects.filter(pk=self.other_candidate.pk).update(updated_at=newer_timestamp)
		HoSoUngVien.objects.filter(pk=self.older_candidate.pk).update(updated_at=older_timestamp - timedelta(hours=1))
		self.matching_candidate.refresh_from_db()
		self.other_candidate.refresh_from_db()
		self.older_candidate.refresh_from_db()

		next_monday = self._next_weekday_datetime(0, hour=9)
		job_end = next_monday.replace(hour=17)
		self.job = TinTuyenDung.objects.create(
			cong_ty=self.company_profile,
			tieu_de="Tuyen Python Backend",
			noi_dung="Can Python, Django va REST API.",
			bat_dau_lam=next_monday,
			ket_thuc_lam=job_end,
			luong_theo_gio=Decimal("120.00"),
			dia_diem_lam_viec="Da Nang",
			trang_thai=TinTuyenDung.TrangThai.DANG_MO,
		)
		self.detail_review_1 = DanhGia.objects.create(
			ung_tuyen=self._create_application(self.matching_candidate),
			nguoi_danh_gia=self.employer_user,
			nguoi_nhan_danh_gia=self.candidate_user,
			diem_so=5,
			nhan_xet="Rat tot",
		)
		self.detail_review_2 = DanhGia.objects.create(
			ung_tuyen=self._create_application(self.matching_candidate),
			nguoi_danh_gia=self.employer_user,
			nguoi_nhan_danh_gia=self.candidate_user,
			diem_so=4,
			nhan_xet="Nhanh nhen",
		)

	def test_list_requires_employer_role(self):
		self.client.force_authenticate(user=self.candidate_user)
		response = self.client.get(reverse("candidate-list"))

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_list_filters_sorts_and_paginates_candidates(self):
		self.client.force_authenticate(user=self.employer_user)
		response = self.client.get(
			reverse("candidate-list"),
			{
				"q": "python",
				"location": "da nang",
				"salary_min": "20000",
				"salary_max": "25000",
				"availability_slots": '["Mon-AM"]',
				"sort": "matching_desc",
			},
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["page"], 1)
		self.assertEqual(response.data["limit"], 20)
		self.assertEqual(response.data["total"], 1)
		result = response.data["results"][0]
		self.assertEqual(result["candidate_id"], self.matching_candidate.ung_vien_id)
		self.assertEqual(result["full_name"], "Nguyen Van A")
		self.assertEqual(result["avatar_url"], "https://cdn.example.com/candidates/a.jpg")
		self.assertEqual(result["primary_skills"], ["Python", "Django", "REST"])
		self.assertEqual(result["location"], "Da Nang")
		self.assertEqual(result["expected_salary"], 22000)
		self.assertGreater(result["matching_score"], 0)
		self.assertIn("updated_at", result)

	def test_updated_desc_sorts_by_recency(self):
		self.client.force_authenticate(user=self.employer_user)
		response = self.client.get(reverse("candidate-list"), {"sort": "updated_desc"})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["results"][0]["candidate_id"], self.other_candidate.ung_vien_id)
		self.assertEqual(response.data["results"][1]["candidate_id"], self.matching_candidate.ung_vien_id)

	def test_matched_candidates_uses_job_score_and_filters(self):
		self.client.force_authenticate(user=self.employer_user)
		response = self.client.get(
			reverse("matched-candidates", kwargs={"job_id": self.job.tin_id}),
			{"q": "python", "sort": "matching_desc"},
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["total"], 2)
		self.assertEqual(response.data["results"][0]["candidate_id"], self.matching_candidate.ung_vien_id)
		self.assertGreater(response.data["results"][0]["matching_score"], response.data["results"][1]["matching_score"])

	def test_candidate_detail_includes_reviews_and_empty_sections(self):
		self.client.force_authenticate(user=self.employer_user)
		response = self.client.get(reverse("candidate-detail", kwargs={"candidate_id": self.matching_candidate.ung_vien_id}))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["candidate_id"], self.matching_candidate.ung_vien_id)
		self.assertEqual(response.data["skills"], ["Python", "Django", "REST"])
		self.assertEqual(response.data["availability_slots"], ["Mon-AM", "Tue-PM"])
		self.assertEqual(response.data["experience"], [])
		self.assertEqual(response.data["certifications"], [])
		self.assertEqual(response.data["review_summary"], {"avg_rating": 4.5, "total_reviews": 2})
		self.assertEqual(len(response.data["reviews"]), 2)

	def test_invalid_availability_slots_returns_bad_request(self):
		self.client.force_authenticate(user=self.employer_user)
		response = self.client.get(reverse("candidate-list"), {"availability_slots": "not-json"})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("availability_slots", response.data)

	def _create_application(self, candidate):
		from modules.applications.models import UngTuyen

		return UngTuyen.objects.create(tin=self.job, ung_vien=candidate)

	@staticmethod
	def _next_weekday_datetime(target_weekday, hour=9):
		today = timezone.localdate()
		days_ahead = (target_weekday - today.weekday()) % 7
		if days_ahead == 0:
			days_ahead = 7
		start_date = today + timedelta(days=days_ahead)
		naive_datetime = datetime.combine(start_date, datetime_time(hour=hour, minute=0))
		return timezone.make_aware(naive_datetime)
