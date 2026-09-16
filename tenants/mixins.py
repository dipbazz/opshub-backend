from typing import TYPE_CHECKING, Any

from django.db.models import QuerySet

from tenants.models import User

if TYPE_CHECKING:
    from rest_framework.generics import GenericAPIView

    _Base = GenericAPIView[Any]
else:
    _Base = object


class TenantScopedQuerySetMixin(_Base):
    def get_queryset(self) -> QuerySet[Any]:
        if not isinstance(self.request.user, User):
            raise TypeError("TenantScopedQuerySetMixin requires an authenticated User")

        return super().get_queryset().filter(tenant=self.request.user.tenant_id)
