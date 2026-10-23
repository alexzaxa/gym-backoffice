from django.contrib import admin

from .models import Visit


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("member", "gym", "checked_in_at", "checked_out_at", "result", "method", "checkout_estimated")
    list_filter = ("gym", "result", "method", "checkout_estimated")
    search_fields = ("member__first_name", "member__last_name", "member__checkin_code")
