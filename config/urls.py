from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

from accounts import views as account_views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="members:list"), name="home"),
    path("signup/", account_views.GymSignupView.as_view(), name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("settings/", account_views.GymSettingsView.as_view(), name="settings"),
    path("staff/", account_views.StaffListView.as_view(), name="staff_list"),
    path("staff/new/", account_views.StaffCreateView.as_view(), name="staff_create"),
    path("members/", include("members.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
