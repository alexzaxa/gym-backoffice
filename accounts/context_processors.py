from .models import Gym


def theme(request):
    """The look chosen by the logged-in user's gym. Pages without a gym use the default."""
    user = getattr(request, "user", None)
    gym = getattr(user, "gym", None) if user and user.is_authenticated else None
    return {"theme": gym.theme if gym else Gym.Theme.BOLD}
