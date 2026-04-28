from rest_framework import serializers

from modules.jobs.models import TinTuyenDung


class TinTuyenDungSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="cong_ty.ten_cong_ty", read_only=True)
    posting_title = serializers.CharField(source="tieu_de", read_only=True)
    job_title = serializers.CharField(source="tieu_de", read_only=True)
    recruitment_type = serializers.SerializerMethodField()
    application_deadline = serializers.SerializerMethodField()
    requirements = serializers.SerializerMethodField()
    benefits = serializers.SerializerMethodField()
    edit_action = serializers.SerializerMethodField()
    delete_action = serializers.SerializerMethodField()
    job_description = serializers.CharField(source="noi_dung", read_only=True)

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


    def to_internal_value(self, data):
        """
        Dịch dữ liệu từ API (Tiếng Anh) sang DB (Tiếng Việt) khi Frontend gọi PUT/PATCH
        """
        # Tạo một bản sao có thể chỉnh sửa của data
        mapped_data = data.copy() if hasattr(data, 'copy') else dict(data)
        
        # Ánh xạ các trường
        if 'title' in mapped_data:
            mapped_data['tieu_de'] = mapped_data.pop('title')
        if 'description' in mapped_data:
            mapped_data['noi_dung'] = mapped_data.pop('description')
        if 'salary' in mapped_data: # Hoặc hourly_rate tùy frontend gửi
            # Chú ý: frontend có thể gửi "50000 / giờ", cần filter lấy số nếu cần, 
            # hoặc frontend phải gửi đúng số (VD: 50000)
            mapped_data['luong_theo_gio'] = mapped_data.pop('salary') 
        if 'status' in mapped_data:
            mapped_data['trang_thai'] = mapped_data.pop('status')
        if 'location' in mapped_data:
            mapped_data['dia_diem_lam_viec'] = mapped_data.pop('location')

        return super().to_internal_value(mapped_data)

    def get_recruitment_type(self, instance):
        return getattr(instance, "hinh_thuc_tuyen_dung", None) or "Chưa cập nhật"

    def get_application_deadline(self, instance):
        deadline = getattr(instance, "ket_thuc_lam", None)
        if deadline is None:
            return None
        return deadline.strftime("%Y-%m-%d %H:%M:%S")

    def get_requirements(self, instance):
        return getattr(instance, "yeu_cau", None) or "Chưa cập nhật"

    def get_benefits(self, instance):
        return getattr(instance, "quyen_loi", None) or "Chưa cập nhật"

    def get_edit_action(self, instance):
        return {
            "label": "Chỉnh sửa thông tin đăng tuyển",
            "available": self._can_manage(instance),
        }

    def get_delete_action(self, instance):
        return {
            "label": "Xóa thông tin ứng đăng tuyển",
            "available": self._can_manage(instance),
        }

    def _can_manage(self, instance):
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return False

        company_user = getattr(getattr(instance, "cong_ty", None), "cong_ty", None)
        return company_user == request.user

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
