from rest_framework import serializers

from modules.jobs.models import TinTuyenDung


class TinTuyenDungSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        raw_data = dict(data)

        tieu_de = data.get("tieu_de") or ""
        noi_dung = data.get("noi_dung") or ""
        luong_theo_gio = data.get("luong_theo_gio")
        trang_thai = data.get("trang_thai") or ""
        dia_diem_lam_viec = data.get("dia_diem_lam_viec") or ""

        data["title"] = tieu_de
        data["description"] = noi_dung
        data["summary"] = self._build_summary(noi_dung)
        data["salary"] = self._format_salary(luong_theo_gio)
        data["status"] = self._format_status(trang_thai)
        data["badges"] = self._build_badges(trang_thai, dia_diem_lam_viec)
        data["openings"] = 1
        data["location"] = dia_diem_lam_viec
        data["raw"] = raw_data

        return data

    @staticmethod
    def _build_summary(description):
        summary = (description or "").strip()
        if len(summary) <= 120:
            return summary
        return f"{summary[:117].rstrip()}..."

    @staticmethod
    def _format_salary(salary_value):
        if salary_value in (None, ""):
            return "Chưa cập nhật"
        return f"{salary_value} / giờ"

    @staticmethod
    def _format_status(status_value):
        status_map = {
            TinTuyenDung.TrangThai.DANG_MO: "Đang mở",
            TinTuyenDung.TrangThai.DA_DONG: "Đã đóng",
        }
        return status_map.get(status_value, status_value or "Không xác định")

    @staticmethod
    def _build_badges(status_value, location_value):
        badges = []
        if status_value:
            badges.append(TinTuyenDungSerializer._format_status(status_value))
        if location_value:
            badges.append(location_value)
        return badges or ["Tuyển dụng"]

    class Meta:
        model = TinTuyenDung
        fields = "__all__"
