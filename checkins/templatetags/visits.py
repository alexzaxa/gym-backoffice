from django import template

register = template.Library()


@register.filter
def hours_minutes(delta):
    """Format a timedelta as '1h 05m' or '45m'."""
    if delta is None:
        return "—"
    minutes = int(delta.total_seconds() // 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m" if hours else f"{minutes}m"
