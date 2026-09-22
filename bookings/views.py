from typing import TYPE_CHECKING, Any

from rest_framework import viewsets
from rest_framework.serializers import BaseSerializer

from bookings.models import Resource
from bookings.serializers import ResourceSerializer
from tenants.mixins import TenantScopedQuerySetMixin
from tenants.models import User
from tenants.permissions import IsTenantManagerOrAbove, IsTenantMember

if TYPE_CHECKING:
    # _SupportsHasPermission exists only in rest_framework-stubs, not in the
    # real installed rest_framework.permissions module at runtime — importing
    # it unconditionally would crash the app. Type-checking only.
    from rest_framework.permissions import _SupportsHasPermission


class ResourceViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet[Resource]):
    serializer_class = ResourceSerializer
    queryset = Resource.objects.all()

    def get_permissions(self) -> "list[_SupportsHasPermission]":
        if self.action in ("list", "retrieve"):
            self.permission_classes = [IsTenantMember]
        else:
            self.permission_classes = [IsTenantManagerOrAbove]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        if not isinstance(self.request.user, User):
            raise TypeError(f"{type(self).__name__} requires an authenticated tenants.User")
        serializer.save(tenant=self.request.user.tenant)
