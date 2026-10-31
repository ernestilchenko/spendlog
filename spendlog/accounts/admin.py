from django.contrib import admin

from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency', 'opening_balance', 'opening_date', 'is_archived', 'user')
