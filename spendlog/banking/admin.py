from django.contrib import admin

from .models import BankAccountLink, BankConnection, IgnoredBankTransaction, PassThroughRule, PendingPassThrough


class BankAccountLinkInline(admin.TabularInline):
    model = BankAccountLink
    extra = 0
    readonly_fields = ('uid', 'iban', 'bank_balance', 'bank_balance_at')


@admin.register(BankConnection)
class BankConnectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'aspsp_name', 'status', 'valid_until', 'last_synced_at')
    readonly_fields = ('state', 'session_id', 'last_error')
    inlines = (BankAccountLinkInline,)


@admin.register(PassThroughRule)
class PassThroughRuleAdmin(admin.ModelAdmin):
    list_display = ('user', 'pattern', 'passed_on_amount', 'match_days')


@admin.register(PendingPassThrough)
class PendingPassThroughAdmin(admin.ModelAdmin):
    list_display = ('user', 'rule', 'amount', 'received_on', 'expires_on')


@admin.register(IgnoredBankTransaction)
class IgnoredBankTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'external_id', 'reason', 'created_at')
