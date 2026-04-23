from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from modules.applications.models import UngTuyen
from modules.chats.models import Chat
from modules.jobs.models import TinTuyenDung
from modules.profiles.models import HoSoCongTy, HoSoUngVien


class ChatApiTests(APITestCase):
	def setUp(self):
		user_model = get_user_model()
		self.employer_user = user_model.objects.create_user(
			email="employer-chat@example.com",
			password="password123",
			vai_tro=user_model.VaiTro.CONG_TY,
		)
		self.candidate_user = user_model.objects.create_user(
			email="candidate-chat@example.com",
			password="password123",
			vai_tro=user_model.VaiTro.UNG_VIEN,
		)
		self.other_candidate_user = user_model.objects.create_user(
			email="candidate-other@example.com",
			password="password123",
			vai_tro=user_model.VaiTro.UNG_VIEN,
		)
		self.other_employer_user = user_model.objects.create_user(
			email="employer-other@example.com",
			password="password123",
			vai_tro=user_model.VaiTro.CONG_TY,
		)

		self.employer_profile = HoSoCongTy.objects.create(
			cong_ty=self.employer_user,
			ten_cong_ty="Cong Ty Chat",
		)
		self.candidate_profile = HoSoUngVien.objects.create(
			ung_vien=self.candidate_user,
			ho_ten="Ung Vien Chat",
			luong_mong_muon=Decimal("20000.00"),
		)
		self.other_candidate_profile = HoSoUngVien.objects.create(
			ung_vien=self.other_candidate_user,
			ho_ten="Ung Vien Khac",
			luong_mong_muon=Decimal("18000.00"),
		)
		self.other_employer_profile = HoSoCongTy.objects.create(
			cong_ty=self.other_employer_user,
			ten_cong_ty="Cong Ty Khac",
		)

		job_start = timezone.now() + timedelta(days=1)
		job_end = job_start + timedelta(days=7)
		self.job = TinTuyenDung.objects.create(
			cong_ty=self.employer_profile,
			tieu_de="Backend Dev",
			noi_dung="Mo ta cong viec",
			bat_dau_lam=job_start,
			ket_thuc_lam=job_end,
			luong_theo_gio=Decimal("120.00"),
			dia_diem_lam_viec="Da Nang",
		)
		UngTuyen.objects.create(tin=self.job, ung_vien=self.candidate_profile)

	def test_chat_requires_authentication(self):
		response = self.client.get(reverse("chat-conversations"))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_employer_can_send_message_to_related_candidate(self):
		self.client.force_authenticate(user=self.employer_user)
		response = self.client.post(
			reverse("chat-messages"),
			{"nguoi_nhan_id": self.candidate_user.id, "noi_dung_tin_nhan": "Xin chao ung vien"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["nguoi_gui"], self.employer_user.id)
		self.assertEqual(response.data["nguoi_nhan"], self.candidate_user.id)
		self.assertEqual(response.data["noi_dung_tin_nhan"], "Xin chao ung vien")
		self.assertTrue(response.data["is_outgoing"])

	def test_send_message_forbidden_when_no_application_relationship(self):
		self.client.force_authenticate(user=self.employer_user)
		response = self.client.post(
			reverse("chat-messages"),
			{"nguoi_nhan_id": self.other_candidate_user.id, "noi_dung_tin_nhan": "Xin chao"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_send_message_forbidden_for_same_role(self):
		self.client.force_authenticate(user=self.employer_user)
		response = self.client.post(
			reverse("chat-messages"),
			{"nguoi_nhan_id": self.other_employer_user.id, "noi_dung_tin_nhan": "Xin chao"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_list_messages_returns_only_current_pair(self):
		Chat.objects.create(
			nguoi_gui=self.employer_user,
			nguoi_nhan=self.candidate_user,
			noi_dung_tin_nhan="Tin nhan 1",
		)
		Chat.objects.create(
			nguoi_gui=self.candidate_user,
			nguoi_nhan=self.employer_user,
			noi_dung_tin_nhan="Tin nhan 2",
		)
		Chat.objects.create(
			nguoi_gui=self.other_employer_user,
			nguoi_nhan=self.other_candidate_user,
			noi_dung_tin_nhan="Khong lien quan",
		)

		self.client.force_authenticate(user=self.employer_user)
		response = self.client.get(reverse("chat-messages"), {"peer_user_id": self.candidate_user.id})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["total"], 2)
		self.assertEqual(len(response.data["results"]), 2)
		self.assertEqual(response.data["results"][0]["noi_dung_tin_nhan"], "Tin nhan 1")
		self.assertEqual(response.data["results"][1]["noi_dung_tin_nhan"], "Tin nhan 2")

	def test_conversation_list_returns_latest_message_by_peer(self):
		Chat.objects.create(
			nguoi_gui=self.employer_user,
			nguoi_nhan=self.candidate_user,
			noi_dung_tin_nhan="Tin cu",
		)
		Chat.objects.create(
			nguoi_gui=self.candidate_user,
			nguoi_nhan=self.employer_user,
			noi_dung_tin_nhan="Tin moi nhat",
		)

		self.client.force_authenticate(user=self.employer_user)
		response = self.client.get(reverse("chat-conversations"))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["total"], 1)
		conversation = response.data["results"][0]
		self.assertEqual(conversation["peer_user_id"], self.candidate_user.id)
		self.assertEqual(conversation["peer_display_name"], "Ung Vien Chat")
		self.assertEqual(conversation["last_message"], "Tin moi nhat")
