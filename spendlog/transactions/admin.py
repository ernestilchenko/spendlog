from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('occurred_at', 'merchant', 'amount', 'kind', 'category', 'source', 'user')
    list_filter = ('kind', 'source')
    search_fields = ('merchant', 'note')
    date_hierarchy = 'occurred_at'
