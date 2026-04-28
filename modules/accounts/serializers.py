from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from modules.accounts.models import NguoiDung


class NguoiDungSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = NguoiDung
        fields = ["id", "email", "password", "vai_tro", "tao_luc"]
        read_only_fields = ["id", "tao_luc"]

    def validate_password(self, value):
        email = self.initial_data.get("email") if isinstance(self.initial_data, dict) else None
        candidate_user = NguoiDung(email=email) if email else None

        try:
            validate_password(value, user=candidate_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return NguoiDung.objects.create_user(password=password, **validated_data)
