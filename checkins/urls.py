from django.urls import path

from . import views

app_name = "checkins"

urlpatterns = [
    path("", views.TodayView.as_view(), name="today"),
    path("kiosk/", views.KioskView.as_view(), name="kiosk"),
    path("kiosk/scan/", views.KioskScanView.as_view(), name="scan"),
    path("member/<int:pk>/toggle/", views.ToggleVisitView.as_view(), name="toggle"),
]
