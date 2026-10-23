from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class GymStaffMixin(LoginRequiredMixin):
    """Requires a logged-in staff user who belongs to a gym and exposes it as self.gym."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.gym_id is None:
            raise PermissionDenied("This account is not linked to a gym.")
        return super().dispatch(request, *args, **kwargs)

    @property
    def gym(self):
        return self.request.user.gym


class OwnerRequiredMixin(GymStaffMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_owner:
            raise PermissionDenied("Only gym owners can do this.")
        return super().dispatch(request, *args, **kwargs)
