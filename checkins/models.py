from datetime import timedelta

from django.db import models
from django.utils import timezone

from accounts.models import Gym
from members.models import Member

# A visit with no scan out is closed this long after check-in and marked as an estimate.
MAX_VISIT_LENGTH = timedelta(hours=3)


class VisitQuerySet(models.QuerySet):
    def allowed(self):
        return self.filter(result=Visit.Result.ALLOWED)

    def open(self):
        return self.allowed().filter(checked_out_at__isnull=True)

    def stale(self, now=None):
        now = now or timezone.now()
        return self.open().filter(checked_in_at__lte=now - MAX_VISIT_LENGTH)

    def close_stale(self, now=None):
        """Close visits nobody scanned out of. Returns how many were closed."""
        closed = 0
        for visit in self.stale(now):
            visit.checked_out_at = visit.checked_in_at + MAX_VISIT_LENGTH
            visit.checkout_estimated = True
            visit.save(update_fields=["checked_out_at", "checkout_estimated"])
            closed += 1
        return closed


class Visit(models.Model):
    """One scan at the door: a check-in (and later its check-out), or a refused entry."""

    class Result(models.TextChoices):
        ALLOWED = "allowed", "Allowed"
        DENIED = "denied", "Denied"

    class Method(models.TextChoices):
        SCAN = "scan", "Scan"
        MANUAL = "manual", "Front desk"

    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="visits")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="visits")
    checked_in_at = models.DateTimeField(default=timezone.now, db_index=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    checkout_estimated = models.BooleanField(
        default=False, help_text="No scan out; closed automatically."
    )
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.SCAN)
    result = models.CharField(max_length=10, choices=Result.choices, default=Result.ALLOWED)
    denied_reason = models.CharField(max_length=200, blank=True)

    objects = VisitQuerySet.as_manager()

    class Meta:
        ordering = ["-checked_in_at"]

    def __str__(self):
        return f"{self.member} at {self.checked_in_at:%Y-%m-%d %H:%M}"

    @property
    def duration(self):
        if self.checked_out_at:
            return self.checked_out_at - self.checked_in_at
        return None

    @property
    def is_open(self):
        return self.result == self.Result.ALLOWED and self.checked_out_at is None
