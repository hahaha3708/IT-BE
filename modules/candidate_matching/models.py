from django.db import models


class JobPersonalityRequirement(models.Model):
    """Lưu yêu cầu về đặc điểm tính cách của công ty cho từng công việc"""
    
    tin = models.OneToOneField(
        "jobs.TinTuyenDung",
        on_delete=models.CASCADE,
        primary_key=True,
        db_column="tin_id",
        related_name="personality_requirement",
    )
    # JSON field lưu danh sách đặc điểm tính cách yêu cầu
    # Ví dụ: {
    #   "traits": [
    #     {"name": "teamwork", "weight": 0.2},
    #     {"name": "proactive", "weight": 0.15},
    #     {"name": "problem_solving", "weight": 0.25},
    #     {"name": "communication", "weight": 0.2},
    #     {"name": "responsibility", "weight": 0.2}
    #   ]
    # }
    traits_required = models.JSONField(
        default=list,
        blank=True,
        help_text="Danh sách đặc điểm tính cách yêu cầu dưới dạng JSON"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "JOB_PERSONALITY_REQUIREMENT"

    def __str__(self):
        return f"Personality Requirement for {self.tin.tieu_de}"


class CandidatePersonalityProfile(models.Model):
    """Lưu hồ sơ đặc điểm tính cách của ứng viên"""
    
    ung_vien = models.OneToOneField(
        "profiles.HoSoUngVien",
        on_delete=models.CASCADE,
        primary_key=True,
        db_column="ung_vien_id",
        related_name="personality_profile",
    )
    # JSON field lưu danh sách đặc điểm tính cách của ứng viên
    # Ví dụ: {
    #   "traits": [
    #     {"name": "teamwork", "score": 0.85},
    #     {"name": "proactive", "score": 0.90},
    #     {"name": "problem_solving", "score": 0.75},
    #     {"name": "communication", "score": 0.80},
    #     {"name": "responsibility", "score": 0.95}
    #   ]
    # }
    traits_profile = models.JSONField(
        default=list,
        blank=True,
        help_text="Hồ sơ đặc điểm tính cách của ứng viên"
    )
    # Niche chuyên ngành (chuyên ngành của ứng viên)
    niche = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Chuyên ngành chính"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "CANDIDATE_PERSONALITY_PROFILE"

    def __str__(self):
        return f"Personality Profile for {self.ung_vien.ho_ten}"
