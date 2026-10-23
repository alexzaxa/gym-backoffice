import secrets

from django.db import models

from accounts.models import Gym

# No 0/O or 1/I so codes are easy to read off a card.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8


def generate_checkin_code():
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


class Member(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        FROZEN = "frozen", "Frozen"
        CANCELLED = "cancelled", "Cancelled"

    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="members")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    photo = models.ImageField(upload_to="member_photos/", blank=True)
    checkin_code = models.CharField(
        max_length=32,
        help_text="Printed on the member's QR card or keyfob.",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["first_name", "last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["gym", "checkin_code"], name="unique_checkin_code_per_gym"
            )
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def initials(self):
        return f"{self.first_name[:1]}{self.last_name[:1]}".upper()

    @property
    def avatar_color(self):
        """Stable 0-5 index so a member keeps the same avatar color."""
        return (self.pk or 0) % 6

    def save(self, *args, **kwargs):
        if not self.checkin_code:
            self.checkin_code = self._unused_code()
        super().save(*args, **kwargs)

    def _unused_code(self):
        while True:
            code = generate_checkin_code()
            if not Member.objects.filter(gym_id=self.gym_id, checkin_code=code).exists():
                return code
