from rest_framework import serializers

from modules.profiles.models import HoSoCongTy, HoSoUngVien


class HoSoUngVienSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoSoUngVien
        fields = [
            "ung_vien",
            "ho_ten",
            "avatar",
            "so_dien_thoai",
            "ky_nang",
            "vi_tri_mong_muon",
            "location",
            "thoi_gian_ranh",
            "availability_slots",
            "luong_mong_muon",
            "updated_at",
        ]
        read_only_fields = ["ung_vien", "updated_at"]


class HoSoCongTySerializer(serializers.ModelSerializer):
    class Meta:
        model = HoSoCongTy
        fields = [
            "cong_ty",
            "ten_cong_ty",
            "linh_vuc",
            "lich_su",
            "lien_he",
            "dia_chi",
        ]
        read_only_fields = ["cong_ty"]
