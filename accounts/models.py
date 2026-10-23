from django.contrib.auth.models import AbstractUser
from django.db import models


class Gym(models.Model):
    """One customer of the product. Every gym's data is kept separate."""

    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    """A staff login. Belongs to exactly one gym (superusers may have none)."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        FRONT_DESK = "front_desk", "Front desk"

    gym = models.ForeignKey(
        Gym, on_delete=models.CASCADE, related_name="staff", null=True, blank=True
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.FRONT_DESK)

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER
