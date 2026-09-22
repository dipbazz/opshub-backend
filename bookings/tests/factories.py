import factory

from bookings.models import Resource
from tenants.tests.factories import TenantFactory


class ResourceFactory(factory.django.DjangoModelFactory[Resource]):
    class Meta:
        model = Resource

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Sequence(lambda n: f"Resource {n}")
    description = factory.Faker("paragraph", nb_sentences=2)
    capacity = 1
