from rest_framework_simplejwt.serializers import AuthUser, TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.views import TokenObtainPairView

from tenants.models import User


class TenantTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: AuthUser) -> Token:
        if not isinstance(user, User):
            raise TypeError(f"{cls.__name__} requires a tenants.User")

        token = super().get_token(user)
        token["tenant_id"] = user.tenant_id
        token["role"] = user.role
        return token


class TenantTokenObtainPairView(TokenObtainPairView):
    serializer_class = TenantTokenObtainPairSerializer
