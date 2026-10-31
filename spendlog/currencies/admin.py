from django.contrib import admin

from .models import ExchangeRate


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('currency', 'date', 'rate')
    list_filter = ('currency',)
