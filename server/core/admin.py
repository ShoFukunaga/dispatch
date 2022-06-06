from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import User, Dispatch


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    pass


@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    fields = (
        'id', 'request_location', 'destination', 'status',
        'contractor', 'requestor',
        'created_at', 'updated_at',
    )
    list_display = (
        'id', 'request_location', 'destination', 'status',
        'contractor', 'requestor',
        'created_at', 'updated_at',
    )
    list_filter = (
        'status',
    )
    readonly_fields = (
        'id', 'created_at', 'updated_at',
    )
