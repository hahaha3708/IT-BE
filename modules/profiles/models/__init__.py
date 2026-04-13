from django.db import models


class HoSoUngVien(models.Model):
	ung_vien = models.OneToOneField(
		"accounts.NguoiDung",
		on_delete=models.CASCADE,
		primary_key=True,
		db_column="ung_vien_id",
		related_name="ho_so_ung_vien",
	)
	ho_ten = models.CharField(max_length=255)
	avatar = models.CharField(max_length=500, null=True, blank=True)
	so_dien_thoai = models.CharField(max_length=20, null=True, blank=True)
	ky_nang = models.TextField(null=True, blank=True)
	vi_tri_mong_muon = models.CharField(max_length=255, null=True, blank=True)
	location = models.CharField(max_length=255, null=True, blank=True)
	thoi_gian_ranh = models.CharField(max_length=255, null=True, blank=True)
	availability_slots = models.JSONField(default=list, blank=True)
	luong_mong_muon = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = "HO_SO_UNG_VIEN"


class HoSoCongTy(models.Model):
	cong_ty = models.OneToOneField(
		"accounts.NguoiDung",
		on_delete=models.CASCADE,
		primary_key=True,
		db_column="cong_ty_id",
		related_name="ho_so_cong_ty",
	)
	ten_cong_ty = models.CharField(max_length=255)
	linh_vuc = models.CharField(max_length=255, null=True, blank=True)
	lich_su = models.TextField(null=True, blank=True)
	lien_he = models.CharField(max_length=255, null=True, blank=True)
	dia_chi = models.TextField(null=True, blank=True)

	class Meta:
		db_table = "HO_SO_CONG_TY"
