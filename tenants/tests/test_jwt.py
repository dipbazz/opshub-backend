"""
Tests for JWT Authentication Token (tenants/auth.py).
Run `uv run pytest tenants/tests/test_jwt.py -v`
"""

import pytest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from tenants.models import Role, Tenant, User

pytestmark = pytest.mark.django_db
client = APIClient()

PASSWORD = "Test@1243"  # noqa: S105
WRONG_PASSWORD = "Test@1213"  # noqa: S105

AUTH_URL = "/api/auth/token/"
REFRESH_URL = "/api/auth/token/refresh/"


def _make_user(*, username: str, tenant: Tenant | None, role: str = Role.MEMBER) -> User:
    return User.objects.create_user(
        username=username,
        password=PASSWORD,
        tenant=tenant,
        role=role,
    )


def _login(username: str, password: str) -> Response:
    response = client.post(AUTH_URL, {"username": username, "password": password})
    return response


class TestTokenObtain:
    def test_valid_credentials_return_access_and_refresh(self) -> None:
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        user = _make_user(username="member", tenant=tenant, role=Role.MEMBER)
        response = _login(user.username, PASSWORD)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_wrong_password_returns_401(self) -> None:
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        user = _make_user(username="member", tenant=tenant, role=Role.MEMBER)
        response = _login(user.username, WRONG_PASSWORD)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unknown_user_returns_401(self) -> None:
        response = _login("unknown", "Not-required")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenClaims:
    def test_access_token_carries_tenant_id_and_role(self) -> None:
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        user = _make_user(username="member", tenant=tenant, role=Role.MEMBER)
        response = _login(user.username, PASSWORD)
        assert response.status_code == status.HTTP_200_OK

        access_token = AccessToken(response.data["access"])
        assert access_token["tenant_id"] == tenant.id
        assert access_token["role"] == Role.MEMBER

    def test_refresh_token_carries_tenant_id_and_role(self) -> None:
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        user = _make_user(username="member", tenant=tenant, role=Role.MEMBER)
        response = _login(user.username, PASSWORD)
        assert response.status_code == status.HTTP_200_OK

        refresh_token = RefreshToken(response.data["refresh"])
        assert refresh_token["tenant_id"] == tenant.id
        assert refresh_token["role"] == Role.MEMBER

    def test_user_with_no_tenant_gets_a_null_tenant_id_claim(self) -> None:
        user = _make_user(username="member", tenant=None, role=Role.MEMBER)
        response = _login(user.username, PASSWORD)
        assert response.status_code == status.HTTP_200_OK

        access_token = AccessToken(response.data["access"])
        assert access_token["tenant_id"] is None

    @pytest.mark.parametrize(
        "role",
        list(Role),
    )
    def test_each_role_is_embedded_correctly(self, role: str) -> None:
        tenant = Tenant.objects.create(name=f"{role.lower()}-Acme", slug=f"{role.lower()}-acme")
        user = _make_user(
            username=f"{role.lower()}-user",
            tenant=tenant,
            role=role,
        )
        response = _login(user.username, PASSWORD)
        assert response.status_code == status.HTTP_200_OK

        access_token = AccessToken(response.data["access"])
        assert access_token["role"] == role


class TestTokenRefresh:
    def test_refreshed_access_token_still_has_the_claims(self) -> None:
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        user = _make_user(username="member", tenant=tenant, role=Role.MEMBER)
        response_token = _login(user.username, PASSWORD)
        assert response_token.status_code == status.HTTP_200_OK
        refresh_token = response_token.data["refresh"]
        response_refresh = client.post(REFRESH_URL, {"refresh": refresh_token})
        assert response_refresh.status_code == status.HTTP_200_OK

        refreshed_access_token = AccessToken(response_refresh.data["access"])
        assert refreshed_access_token["tenant_id"] == tenant.id
        assert refreshed_access_token["role"] == Role.MEMBER
