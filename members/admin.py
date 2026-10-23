from django.contrib import admin

from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "gym", "status", "checkin_code", "email", "phone")
    list_filter = ("gym", "status")
    search_fields = ("first_name", "last_name", "email", "checkin_code")
