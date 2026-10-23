from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from accounts.mixins import GymStaffMixin
from members.models import Member

from .models import Visit
from .services import record_scan, toggle_visit


class KioskView(GymStaffMixin, TemplateView):
    """Full-screen page for a tablet or PC at the door. Scanners type the code and press Enter."""

    template_name = "checkins/kiosk.html"


class KioskScanView(GymStaffMixin, View):
    def post(self, request):
        outcome = record_scan(self.gym, request.POST.get("code", ""))
        return render(request, "checkins/_kiosk_result.html", {"outcome": outcome})


class TodayView(GymStaffMixin, TemplateView):
    template_name = "checkins/today.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        visits = Visit.objects.filter(gym=self.gym)
        visits.close_stale()
        start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        today = visits.filter(checked_in_at__gte=start).select_related("member")
        ctx["inside"] = visits.open().select_related("member").order_by("checked_in_at")
        ctx["today"] = today
        ctx["today_count"] = today.filter(result=Visit.Result.ALLOWED).values("member").distinct().count()
        ctx["denied_count"] = today.filter(result=Visit.Result.DENIED).count()
        return ctx


class ToggleVisitView(GymStaffMixin, View):
    """Front desk checks a member in or out by hand."""

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk, gym=self.gym)
        outcome = toggle_visit(member, method=Visit.Method.MANUAL)
        if outcome.kind == "denied":
            messages.error(request, f"{member.full_name} can't check in: {outcome.message.lower()}.")
        elif outcome.kind == "out":
            messages.success(request, f"{member.full_name} checked out.")
        elif outcome.kind == "repeat":
            messages.success(request, f"{member.full_name} is already checked in.")
        else:
            messages.success(request, f"{member.full_name} checked in.")
        return redirect(request.POST.get("next") or "checkins:today")
