from rest_framework.permissions import BasePermission

from modules.accounts.models import NguoiDung


class IsEmployer(BasePermission):
	message = "Employer role required"

	def has_permission(self, request, view):
		user = getattr(request, "user", None)
		return bool(user and user.is_authenticated and getattr(user, "vai_tro", None) == NguoiDung.VaiTro.CONG_TY)
