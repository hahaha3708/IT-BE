from rest_framework import serializers

from modules.profiles.models import HoSoCongTy, HoSoUngVien


class HoSoUngVienSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()

    class Meta:
        model = HoSoUngVien
        fields = [
            "ung_vien",
            "email",
            "ho_ten",
            "avatar",
            "so_dien_thoai",
            "ky_nang",
            "vi_tri_mong_muon",
            "location",
            "thoi_gian_ranh",
            "availability_slots",
            "luong_mong_muon",
            "gioi_thieu",
            "hoc_van",
            "chung_chi",
            "ngoai_ngu",
            "du_an",
            "updated_at",
        ]
        read_only_fields = ["ung_vien", "email", "updated_at"]

    def get_email(self, obj):
        """Retrieve email từ related NguoiDung object"""
        return obj.ung_vien.email if obj.ung_vien else None


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
