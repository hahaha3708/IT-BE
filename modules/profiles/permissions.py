from rest_framework.permissions import BasePermission

from modules.accounts.models import NguoiDung


class IsCandidateSelf(BasePermission):
    """
    Cho phép ứng viên xem/sửa chỉ hồ sơ của chính mình.
    """
    message = "Bạn chỉ có thể xem hoặc chỉnh sửa hồ sơ của chính mình."

    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        if getattr(user, "vai_tro", None) != NguoiDung.VaiTro.UNG_VIEN:
            return False

        # obj là HoSoUngVien instance
        return obj.ung_vien_id == user.id


class IsEmployerOrCandidateSelf(BasePermission):
    """
    Cho phép ứng viên xem hồ sơ của chính mình hoặc nhà tuyển dụng xem bất kỳ hồ sơ nào.
    """
    message = "Bạn không có quyền xem hồ sơ này."

    def has_object_permission(self, request, view, obj):
        # Nếu là ứng viên, chỉ xem được hồ sơ của chính mình
        if request.user.vai_tro == NguoiDung.VaiTro.UNG_VIEN:
            return obj.ung_vien == request.user
        
        # Nếu là nhà tuyển dụng, có thể xem bất kỳ hồ sơ nào
        if request.user.vai_tro == NguoiDung.VaiTro.CONG_TY:
            return True
        
        # Admin xem được tất cả
        return request.user.is_superuser
