import factory

from tenants.models import Role, Tenant, User


class TenantFactory(factory.django.DjangoModelFactory[Tenant]):
    class Meta:
        model = Tenant

    name = factory.Faker("company")
    slug = factory.Sequence(lambda n: f"tenant-{n}")


class UserFactory(factory.django.DjangoModelFactory[User]):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"username-{n}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    tenant = factory.SubFactory(TenantFactory)
    role = Role.MEMBER
