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
