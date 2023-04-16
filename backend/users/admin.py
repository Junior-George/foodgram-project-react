from django.contrib import admin

from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'last_name',
        'first_name',
    )
    list_filter = (
        'email',
        'username'
    )
    search_fields = (
        'email',
        'username'
    )
    emty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
