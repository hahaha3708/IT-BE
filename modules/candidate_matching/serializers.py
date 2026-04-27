from rest_framework import serializers
from modules.jobs.models import TinTuyenDung
from modules.profiles.models import HoSoUngVien, HoSoCongTy
from modules.candidate_matching.models import JobPersonalityRequirement, CandidatePersonalityProfile


class CandidateMatchSerializer(serializers.Serializer):
    """Serializer cho thông tin ứng viên phù hợp"""
    
    ung_vien_id = serializers.IntegerField()
    ho_ten = serializers.CharField()
    avatar = serializers.CharField(allow_null=True)
    ky_nang = serializers.CharField(allow_null=True)
    vi_tri_mong_muon = serializers.CharField(allow_null=True)
    location = serializers.CharField(allow_null=True)
    luong_mong_muon = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    
    # Matching scores
    skill_match_score = serializers.FloatField(help_text="Điểm match kỹ năng (0-1)")
    personality_match_score = serializers.FloatField(help_text="Điểm match tính cách (0-1)")
    overall_match_score = serializers.FloatField(help_text="Điểm match tổng thể (0-1)")
    
    matched_skills = serializers.ListField(
        child=serializers.CharField(),
        help_text="Danh sách kỹ năng phù hợp"
    )
    matched_traits = serializers.ListField(
        child=serializers.DictField(),
        help_text="Danh sách tính cách phù hợp"
    )


class JobMatchingResultSerializer(serializers.Serializer):
    """Serializer cho kết quả tìm kiếm ứng viên phù hợp"""
    
    job_id = serializers.IntegerField()
    job_title = serializers.CharField()
    company_name = serializers.CharField()
    total_candidates = serializers.IntegerField(help_text="Tổng số ứng viên phù hợp")
    eligible_candidates = serializers.IntegerField(help_text="Số ứng viên phù hợp (80%+ match)")
    candidates = CandidateMatchSerializer(many=True, help_text="Danh sách ứng viên phù hợp")


class JobPersonalityRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPersonalityRequirement
        fields = ['tin_id', 'traits_required', 'updated_at']


class CandidatePersonalityProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidatePersonalityProfile
        fields = ['ung_vien_id', 'traits_profile', 'niche', 'updated_at']
