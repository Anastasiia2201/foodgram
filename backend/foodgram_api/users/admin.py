from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + (
        "avatar",
        "role",
    )
    list_editable = UserAdmin.list_editable + (
        "avatar",
        "role",
    )
    search_fields = (
        "email",
        "username",
        "last_name",
        "first_name",
    )
