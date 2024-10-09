from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('avatar',)
    list_editable = UserAdmin.list_editable + ('avatar',)
    search_fields = ('email', 'username',) 


admin.site.register(User, CustomUserAdmin)
