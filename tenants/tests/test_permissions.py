"""
Tests for tenants/permissions.py (IsTenantMember, IsTenantManagerOrAbove,
IsTenantAdmin).
Run `uv run pytest tenants/tests/test_permissions.py -v`
"""

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from bookings.models import Resource
from tenants.models import Role, Tenant, User
from tenants.permissions import IsTenantAdmin, IsTenantManagerOrAbove, IsTenantMember

pytestmark = pytest.mark.django_db

factory = APIRequestFactory()
view = APIView()  # has_permission/has_object_permission don't inspect it here


def _authenticated_request(user: User) -> Request:
    django_request = factory.get("/")
    force_authenticate(django_request, user=user)
    return Request(django_request)


def _make_user(*, username: str, tenant: Tenant | None, role: str = Role.MEMBER) -> User:
    return User.objects.create_user(
        username=username,
        password="irrelevant-for-this-test",  # noqa: S106
        tenant=tenant,
        role=role,
    )


class TestIsTenantMember:
    def test_user_with_a_tenant_is_allowed(self) -> None:
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        user = _make_user(username="member", tenant=tenant, role=Role.MEMBER)
        request = _authenticated_request(user)

        assert IsTenantMember().has_permission(request=request, view=view)

    def test_user_with_no_tenant_is_denied(self) -> None:
        user = _make_user(username="no-tenant", tenant=None, role=Role.MEMBER)
        request = _authenticated_request(user)

        assert IsTenantMember().has_permission(request=request, view=view) is False


class TestIsTenantManagerOrAbove:
    @pytest.mark.parametrize(
        ("role", "expected"),
        [(Role.MEMBER, False), (Role.MANAGER, True), (Role.ADMIN, True)],
    )
    def test_role_gate(self, role: str, expected: bool) -> None:  # noqa: FBT001
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        user = _make_user(username=f"user-{role.lower()}", tenant=tenant, role=role)
        request = _authenticated_request(user)

        assert IsTenantManagerOrAbove().has_permission(request=request, view=view) is expected


class TestIsTenantAdmin:
    @pytest.mark.parametrize(
        ("role", "expected"),
        [(Role.MEMBER, False), (Role.MANAGER, False), (Role.ADMIN, True)],
    )
    def test_role_gate(self, role: str, expected: bool) -> None:  # noqa: FBT001
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        user = _make_user(username=f"user-{role.lower()}", tenant=tenant, role=role)
        request = _authenticated_request(user)

        assert IsTenantAdmin().has_permission(request=request, view=view) is expected


class TestObjectLevelTenantGuard:
    """
    has_object_permission's tenant-match check is defined once, on the
    shared base class all three permissions above inherit from — so
    exercising it through any one of them (IsTenantMember here) covers
    all three.
    """

    def test_denies_an_object_belonging_to_a_different_tenant(self) -> None:
        tenant_a = Tenant.objects.create(name="Acme", slug="acme")
        tenant_b = Tenant.objects.create(name="Globex", slug="globex")
        user_a = _make_user(username="user-a", tenant=tenant_a, role=Role.ADMIN)
        resource_b = Resource.objects.create(tenant=tenant_b, name="Room B")
        request = _authenticated_request(user_a)

        assert (
            IsTenantMember().has_object_permission(request=request, view=view, obj=resource_b)
            is False
        )

    def test_allows_an_object_belonging_to_the_same_tenant(self) -> None:
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        user = _make_user(username="user-a", tenant=tenant, role=Role.MEMBER)
        resource = Resource.objects.create(tenant=tenant, name="Room A")
        request = _authenticated_request(user)

        assert (
            IsTenantMember().has_object_permission(request=request, view=view, obj=resource) is True
        )
