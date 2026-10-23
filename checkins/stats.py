from datetime import timedelta

from django.utils import timezone

from .models import Visit


def member_stats(member, now=None):
    """Visit numbers shown on the member page (and later in the member portal)."""
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    visits = list(Visit.objects.allowed().filter(member=member).order_by("checked_in_at"))
    month_start = local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_start = (local_now - timedelta(days=local_now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    days = {timezone.localtime(v.checked_in_at).date() for v in visits}
    closed = [v for v in visits if v.duration]
    total = sum((v.duration for v in closed), timedelta())

    return {
        "total_visits": len(days),
        "visits_this_month": len({d for d in days if d >= month_start.date()}),
        "time_this_week": sum((v.duration for v in closed if v.checked_in_at >= week_start), timedelta()),
        "average_visit": total / len(closed) if closed else None,
        "week_streak": _week_streak(days, local_now.date()),
    }


def _week_streak(days, today):
    """Weeks in a row with at least one visit, counting back from this week (or last week)."""
    weeks = {d - timedelta(days=d.weekday()) for d in days}
    week = today - timedelta(days=today.weekday())
    if week not in weeks:
        week -= timedelta(weeks=1)
    streak = 0
    while week in weeks:
        streak += 1
        week -= timedelta(weeks=1)
    return streak
