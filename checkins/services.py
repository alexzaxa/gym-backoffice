from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from members.models import Member

from .models import Visit

# A second scan this soon after checking in is treated as an accidental double scan.
DOUBLE_SCAN_WINDOW = timedelta(minutes=2)

DENY_REASONS = {
    Member.Status.FROZEN: "Membership is frozen",
    Member.Status.CANCELLED: "Membership is cancelled",
}


@dataclass
class ScanOutcome:
    kind: str  # "in", "out", "repeat", "denied" or "unknown"
    member: Member | None = None
    visit: Visit | None = None
    message: str = ""


@transaction.atomic
def record_scan(gym, code, method=Visit.Method.SCAN, now=None):
    """Check a member in or out by their check-in code."""
    now = now or timezone.now()
    code = (code or "").strip().upper()
    member = Member.objects.filter(gym=gym, checkin_code=code).first() if code else None
    if member is None:
        return ScanOutcome("unknown", message="Code not recognised. Please see the front desk.")
    return toggle_visit(member, method=method, now=now)


@transaction.atomic
def toggle_visit(member, method=Visit.Method.SCAN, now=None):
    """Check the member out if they're in, otherwise try to check them in."""
    now = now or timezone.now()
    visits = Visit.objects.select_for_update().filter(member=member)
    visits.close_stale(now)

    open_visit = visits.open().first()
    if open_visit:
        if now - open_visit.checked_in_at < DOUBLE_SCAN_WINDOW:
            return ScanOutcome("repeat", member, open_visit, "Already checked in")
        open_visit.checked_out_at = now
        open_visit.save(update_fields=["checked_out_at"])
        return ScanOutcome("out", member, open_visit, "See you next time")

    if member.status in DENY_REASONS:
        reason = DENY_REASONS[member.status]
        visit = Visit.objects.create(
            gym=member.gym, member=member, checked_in_at=now, method=method,
            result=Visit.Result.DENIED, denied_reason=reason,
        )
        return ScanOutcome("denied", member, visit, reason)

    visit = Visit.objects.create(gym=member.gym, member=member, checked_in_at=now, method=method)
    return ScanOutcome("in", member, visit, "Welcome")
