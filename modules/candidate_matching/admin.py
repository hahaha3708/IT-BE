from django.contrib import admin
from modules.candidate_matching.models import JobPersonalityRequirement, CandidatePersonalityProfile


@admin.register(JobPersonalityRequirement)
class JobPersonalityRequirementAdmin(admin.ModelAdmin):
    list_display = ('tin_id', 'updated_at')
    search_fields = ('tin__tieu_de',)
    readonly_fields = ('updated_at',)


@admin.register(CandidatePersonalityProfile)
class CandidatePersonalityProfileAdmin(admin.ModelAdmin):
    list_display = ('ung_vien_id', 'niche', 'updated_at')
    search_fields = ('ung_vien__ho_ten', 'niche')
    readonly_fields = ('updated_at',)
