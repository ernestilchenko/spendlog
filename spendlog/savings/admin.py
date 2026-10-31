from django.contrib import admin

from .models import SavingsEntry, SavingsGoal


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_amount', 'target_date', 'is_archived', 'user')


@admin.register(SavingsEntry)
class SavingsEntryAdmin(admin.ModelAdmin):
    list_display = ('occurred_at', 'goal', 'kind', 'amount', 'currency', 'amount_pln', 'user')
    list_filter = ('kind', 'currency')
