from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import GymSignupForm, StaffCreateForm
from .mixins import OwnerRequiredMixin


class GymSignupView(CreateView):
    form_class = GymSignupForm
    template_name = "accounts/signup.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("members:list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f"Welcome! {user.gym.name} is set up.")
        return redirect("members:list")


class StaffListView(OwnerRequiredMixin, ListView):
    template_name = "accounts/staff_list.html"
    context_object_name = "staff"

    def get_queryset(self):
        return self.gym.staff.order_by("first_name", "username")


class StaffCreateView(OwnerRequiredMixin, CreateView):
    form_class = StaffCreateForm
    template_name = "accounts/staff_form.html"
    success_url = reverse_lazy("staff_list")

    def form_valid(self, form):
        form.instance.gym = self.gym
        messages.success(self.request, "Staff login created.")
        return super().form_valid(form)
