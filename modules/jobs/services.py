from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework.exceptions import ValidationError

from modules.jobs.models import TinTuyenDung


DEFAULT_STATUS = TinTuyenDung.TrangThai.DANG_MO
ALLOWED_STATUSES = {choice for choice, _label in TinTuyenDung.TrangThai.choices}


def apply_job_filters(queryset, query_params):
	status = (query_params.get("trang_thai") or "").strip() or DEFAULT_STATUS
	if status not in ALLOWED_STATUSES:
		raise ValidationError({"trang_thai": "Gia tri trang_thai khong hop le."})
	queryset = queryset.filter(trang_thai=status)

	keyword = (query_params.get("q") or "").strip()
	if keyword:
		queryset = queryset.filter(Q(tieu_de__icontains=keyword) | Q(noi_dung__icontains=keyword))

	location = (query_params.get("dia_diem") or "").strip()
	if location:
		queryset = queryset.filter(dia_diem_lam_viec__icontains=location)

	wage_min = (query_params.get("luong_min") or "").strip()
	if wage_min:
		try:
			minimum_salary = Decimal(wage_min)
		except InvalidOperation as exc:
			raise ValidationError({"luong_min": "luong_min phai la so hop le."}) from exc
		queryset = queryset.filter(luong_theo_gio__gte=minimum_salary)

	return queryset
