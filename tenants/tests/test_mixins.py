"""
Tests for TenantScopedQuerySetMixin (tenants/mixins.py).
Run `uv run pytest tenants/tests/test_mixins.py -v`
"""

import pytest
from rest_framework import serializers, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from bookings.models import Resource
from tenants.mixins import TenantScopedQuerySetMixin
from tenants.models import Tenant, User

pytestmark = pytest.mark.django_db

factory = APIRequestFactory()


# --- Test-only view + serializer --------------------------------------
# ResourceSerializer/ResourceViewSet don't exist yet (Day 3). This is a
# throwaway view that wires up ONLY the mixin, so these tests exercise
# TenantScopedQuerySetMixin in isolation and won't need rewriting once
# the real views land.


class _ResourceSerializer(serializers.ModelSerializer[Resource]):
    class Meta:
        model = Resource
        fields = ["id", "name", "tenant"]


class _TenantScopedResourceListView(TenantScopedQuerySetMixin, ListAPIView[Resource]):
    queryset = Resource.objects.all()
    serializer_class = _ResourceSerializer


# --- Helpers -------------------------------------------------------------


def _make_tenant_with_user_and_resource(
    *, tenant_name: str, resource_name: str
) -> tuple[Tenant, User, Resource]:
    """Creates one tenant, one user in it, and one resource owned by it."""
    tenant = Tenant.objects.create(name=tenant_name, slug=tenant_name.lower())
    user = User.objects.create_user(
        username=f"user-{tenant_name.lower()}",
        password="irrelevant-for-this-test",  # noqa: S106
        tenant=tenant,
    )
    resource = Resource.objects.create(tenant=tenant, name=resource_name)
    return tenant, user, resource


def _call_view_as(user: User | None) -> Response:
    request = factory.get("/resources/")
    if user is not None:
        force_authenticate(request, user=user)
    view = _TenantScopedResourceListView.as_view()
    return view(request)


# --- Tests -----------------------------------------------------------------


class TestTenantScopedQuerySetMixin:
    def test_user_sees_only_their_own_tenants_resources(self) -> None:
        """The core promise of the mixin: cross-tenant rows never leak in."""
        _tenant_a, user_a, resource_a = _make_tenant_with_user_and_resource(
            tenant_name="Acme", resource_name="Room A"
        )
        _tenant_b, _user_b, resource_b = _make_tenant_with_user_and_resource(
            tenant_name="Globex", resource_name="Room B"
        )

        response = _call_view_as(user_a)

        assert response.status_code == status.HTTP_200_OK
        returned_ids = {row["id"] for row in response.data["results"]}
        assert resource_a.id in returned_ids
        assert resource_b.id not in returned_ids

    def test_superuser_with_no_tenant_sees_empty_list_not_an_error(self) -> None:
        user = User.objects.create_superuser(username="root", password="irrelevant")  # noqa: S106
        Tenant.objects.create(name="Acme", slug="acme")  # a tenant exists but owns nothing here
        Resource.objects.create(
            tenant=Tenant.objects.create(name="Globex", slug="globex"), name="Room B"
        )

        response = _call_view_as(user)
        assert (response.status_code == status.HTTP_200_OK) and (response.data["results"] == [])

    def test_unauthenticated_request_is_rejected_before_the_mixin_runs(self) -> None:
        """
        IsAuthenticated is the global DEFAULT_PERMISSION_CLASSES
        (config/settings/base.py). It runs in DRF's `initial()`, before
        get_queryset() is ever called — so an anonymous request should
        never reach the mixin's isinstance check at all.
        """
        response = _call_view_as(user=None)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
