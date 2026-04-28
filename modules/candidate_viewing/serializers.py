from rest_framework import serializers

from modules.candidate_viewing.services import (
	build_avatar_url,
	build_review_items,
	build_review_summary,
	decimal_to_number,
	format_datetime,
	parse_candidate_slots,
	parse_skill_list,
)


class CandidateListItemSerializer(serializers.Serializer):
	def to_representation(self, instance):
		request = self.context.get("request")
		primary_skills = parse_skill_list(instance.ky_nang)[:3]
		matching_score = getattr(instance, "_matching_score", 0.0)

		return {
			"candidate_id": instance.ung_vien_id,
			"full_name": instance.ho_ten,
			"avatar_url": build_avatar_url(instance, request),
			"primary_skills": primary_skills,
			"location": instance.location,
			"expected_salary": decimal_to_number(instance.luong_mong_muon),
			"matching_score": round(float(matching_score), 1),
			"updated_at": format_datetime(instance.updated_at),
		}


class CandidateDetailSerializer(serializers.Serializer):
	def to_representation(self, instance):
		request = self.context.get("request")
		reviews = self.context.get("reviews", [])
		review_summary = self.context.get("review_summary", build_review_summary([]))

		return {
			"candidate_id": instance.ung_vien_id,
			"full_name": instance.ho_ten,
			"avatar_url": build_avatar_url(instance, request),
			"location": instance.location,
			"expected_salary": decimal_to_number(instance.luong_mong_muon),
			"skills": parse_skill_list(instance.ky_nang),
			"availability_slots": parse_candidate_slots(instance),
			"experience": [],
			"review_summary": review_summary,
			"reviews": build_review_items(reviews),
			"certifications": [],
		}


class CandidateEvaluationSerializer(serializers.Serializer):
	candidate_id = serializers.IntegerField(source="ung_vien_id", read_only=True)
	full_name = serializers.CharField(source="ho_ten", read_only=True)
	email = serializers.EmailField(source="ung_vien.email", read_only=True)
	phone_number = serializers.CharField(source="so_dien_thoai", read_only=True)
	position = serializers.SerializerMethodField()
	applied_date = serializers.SerializerMethodField()
	status = serializers.SerializerMethodField()
	rating = serializers.SerializerMethodField()
	comment = serializers.SerializerMethodField()
	cv_url = serializers.CharField(source="avatar", read_only=True)

	def get_position(self, instance):
		app = self.context.get("application")
		return app.tin.tieu_de if app else "Chưa ứng tuyển"

	def get_applied_date(self, instance):
		app = self.context.get("application")
		return app.thoi_gian_ung_tuyen.strftime("%Y-%m-%d") if app else None

	def get_status(self, instance):
		app = self.context.get("application")
		return app.trang_thai if app else None

	def get_rating(self, instance):
		review = self.context.get("review")
		return review.diem_so if review else 0

	def get_comment(self, instance):
		review = self.context.get("review")
		return review.nhan_xet if review else ""
