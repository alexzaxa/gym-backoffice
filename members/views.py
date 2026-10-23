from django.contrib import messages
from django.db.models import Count, Q
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import GymStaffMixin
from checkins.stats import member_stats

from .forms import MemberForm
from .models import Member


class GymMemberQuerysetMixin(GymStaffMixin):
    def get_queryset(self):
        return Member.objects.filter(gym=self.gym)


class MemberListView(GymMemberQuerysetMixin, ListView):
    template_name = "members/member_list.html"
    context_object_name = "members"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(phone__icontains=q)
                | Q(checkin_code__iexact=q)
            )
        status = self.request.GET.get("status", "")
        if status in Member.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_template_names(self):
        # HTMX live search only swaps the table.
        if self.request.headers.get("HX-Request"):
            return ["members/_member_table.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["statuses"] = Member.Status.choices
        counts = dict(
            Member.objects.filter(gym=self.gym)
            .values_list("status")
            .annotate(n=Count("id"))
        )
        ctx["status_counts"] = [(label, counts.get(value, 0)) for value, label in Member.Status.choices]
        return ctx


class MemberFormMixin(GymMemberQuerysetMixin):
    form_class = MemberForm
    template_name = "members/member_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["gym"] = self.gym
        return kwargs

    def get_success_url(self):
        return reverse("members:detail", args=[self.object.pk])


class MemberCreateView(MemberFormMixin, CreateView):
    def form_valid(self, form):
        messages.success(self.request, "Member added.")
        return super().form_valid(form)


class MemberUpdateView(MemberFormMixin, UpdateView):
    def form_valid(self, form):
        messages.success(self.request, "Member updated.")
        return super().form_valid(form)


class MemberDetailView(GymMemberQuerysetMixin, DetailView):
    template_name = "members/member_detail.html"
    context_object_name = "member"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.object.visits.close_stale()
        ctx["stats"] = member_stats(self.object)
        ctx["recent_visits"] = self.object.visits.all()[:10]
        ctx["is_inside"] = self.object.visits.open().exists()
        return ctx
