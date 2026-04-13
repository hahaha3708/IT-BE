from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('profiles', '0001_initial'),
	]

	operations = [
		migrations.AddField(
			model_name='hosoungvien',
			name='avatar',
			field=models.CharField(blank=True, max_length=500, null=True),
		),
		migrations.AddField(
			model_name='hosoungvien',
			name='availability_slots',
			field=models.JSONField(blank=True, default=list),
		),
		migrations.AddField(
			model_name='hosoungvien',
			name='location',
			field=models.CharField(blank=True, max_length=255, null=True),
		),
		migrations.AddField(
			model_name='hosoungvien',
			name='updated_at',
			field=models.DateTimeField(auto_now=True),
		),
	]
