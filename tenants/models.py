from django.contrib.auth.models import AbstractUser
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tenant(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    MANAGER = "MANAGER", "Manager"
    MEMBER = "MEMBER", "Member"


class User(AbstractUser):
    tenant = models.ForeignKey(
        "Tenant", on_delete=models.CASCADE, related_name="users", null=True, blank=True
    )
    role = models.CharField(choices=Role, max_length=20, default=Role.MEMBER)
