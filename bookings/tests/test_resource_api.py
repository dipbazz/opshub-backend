"""
Tests for ResourceSerializer/ResourceViewSet (bookings/serializers.py,
bookings/views.py).
Run `uv run pytest bookings/tests/test_resource_api.py -v`
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from bookings.models import Resource
from bookings.tests.factories import ResourceFactory
from tenants.models import Role, User
from tenants.tests.factories import TenantFactory, UserFactory

pytestmark = pytest.mark.django_db

RESOURCES_URL = "/api/resources/"


def _client_as(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _detail_url(resource_id: int) -> str:
    return f"{RESOURCES_URL}{resource_id}/"


class TestResourceList:
    def test_member_sees_only_their_own_tenants_resources(self) -> None:
        """Checklist #1/#2: tenant isolation on list."""
        resource_a = ResourceFactory.create()
        member = UserFactory.create(tenant=resource_a.tenant, role=Role.MEMBER)
        resource_b = ResourceFactory.create()
        response = _client_as(member).get(RESOURCES_URL)

        assert response.status_code == status.HTTP_200_OK

        data = response.data["results"]
        returned_ids = {row["id"] for row in data}
        assert resource_a.id in returned_ids
        assert resource_b.id not in returned_ids

    def test_member_gets_404_retrieving_another_tenants_resource(self) -> None:
        """Checklist #3: 404, not 403 — consistent with TenantScopedQuerySetMixin."""
        resource = ResourceFactory.create()
        member = UserFactory.create(role=Role.MEMBER)
        response = _client_as(member).get(_detail_url(resource.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestResourceCreate:
    def test_member_cannot_create_a_resource(self) -> None:
        """Checklist #4: role gate — creating/managing the resource pool is Manager+."""
        member = UserFactory.create(role=Role.MEMBER)
        response = _client_as(member).post(
            RESOURCES_URL,
            {
                "name": "Test resource by member",
                "description": "This is a test resource to check if a member can create it.",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_can_create_a_resource(self) -> None:
        """Checklist #5."""
        manager = UserFactory.create(role=Role.MANAGER)
        response = _client_as(manager).post(
            RESOURCES_URL,
            {
                "name": "Test resource by manager",
                "description": "This is a test resource to check if a manager can create it.",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Resource.objects.filter(tenant=manager.tenant).count() == 1

    def test_created_resource_tenant_is_always_the_requesting_users_tenant(self) -> None:
        """
        Checklist #6 — the one that matters most: POST a different `tenant` id
        in the body and assert the created resource's tenant is still
        request.user.tenant, not the spoofed value. This is the
        serializer-level enforcement test (tenant read-only on the serializer).
        """
        manager = UserFactory.create(role=Role.MANAGER)
        other_tenant = TenantFactory.create()

        response = _client_as(manager).post(
            RESOURCES_URL,
            {
                "tenant": other_tenant.id,
                "name": "The resource by manager",
                "description": "The resource created by manager login but by assigning"
                + " other tenant to prove it is not created.",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["tenant"] == manager.tenant_id
        assert Resource.objects.filter(tenant=manager.tenant).count() == 1
        assert Resource.objects.filter(tenant=other_tenant).count() == 0

    def test_manager_cannot_create_a_resource_with_zero_capacity(self) -> None:
        """Checklist #7."""
        manager = UserFactory.create(role=Role.MANAGER)
        response = _client_as(manager).post(
            RESOURCES_URL,
            {
                "name": "Test resource by manager",
                "description": "This is a test resource to check for 0 capacity.",
                "capacity": 0,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Resource.objects.filter(tenant=manager.tenant).count() == 0
        assert "capacity" in response.data
