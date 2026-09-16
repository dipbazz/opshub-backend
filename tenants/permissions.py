from typing import Protocol

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from tenants.models import Role, User

_ROLE_RANK: dict[str, int] = {
    Role.MEMBER: 0,
    Role.MANAGER: 1,
    Role.ADMIN: 2,
}


class _TenantScoped(Protocol):
    tenant_id: int


class _TenantRolePermission(BasePermission):
    minimum_rank: int

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not isinstance(request.user, User):
            return False

        if request.user.tenant_id is None:
            return False
        return _ROLE_RANK[request.user.role] >= self.minimum_rank

    def has_object_permission(self, request: Request, view: APIView, obj: _TenantScoped) -> bool:
        if not isinstance(request.user, User):
            return False

        return bool(obj.tenant_id == request.user.tenant_id)


class IsTenantMember(_TenantRolePermission):
    minimum_rank = _ROLE_RANK[Role.MEMBER]


class IsTenantManagerOrAbove(_TenantRolePermission):
    minimum_rank = _ROLE_RANK[Role.MANAGER]


class IsTenantAdmin(_TenantRolePermission):
    minimum_rank = _ROLE_RANK[Role.ADMIN]
