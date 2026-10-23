from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Gym, User


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "created_at")
    search_fields = ("name",)


@admin.register(User)
class StaffUserAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "gym", "role", "is_superuser")
    list_filter = ("role", "gym")
    fieldsets = UserAdmin.fieldsets + (("Gym", {"fields": ("gym", "role")}),)
