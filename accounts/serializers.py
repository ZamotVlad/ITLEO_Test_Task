from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import User
from accounts.roles import Roles


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "first_name",
            "last_name",
            "telegram_chat_id",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_role(self, value):
        request_user = self.context["request"].user

        # Owner може призначати будь-яку роль
        allowed_for_manager = [Roles.STUDENT, Roles.PARENT]

        if request_user.role != Roles.OWNER and value not in allowed_for_manager:
            raise serializers.ValidationError(
                "Менеджер може призначати лише ролі 'student' або 'parent'."
            )

        # При оновленні існуючого юзера — лише owner може змінити роль
        if self.instance and value != self.instance.role and request_user.role != Roles.OWNER:
            raise serializers.ValidationError(
                "Лише owner може змінювати ролі існуючих користувачів."
            )

        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Стандартний JWT-логін, але у відповіді одразу id/username/role —
    фронтенду не треба робити другий запит на /api/me/ одразу після логіну.
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        data["id"] = self.user.id
        data["username"] = self.user.username
        data["role"] = self.user.role
        return data
