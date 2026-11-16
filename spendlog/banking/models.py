from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from spendlog.accounts.models import Account
from spendlog.core.choices import BankConnectionStatus
from spendlog.core.models import TimeStampedModel


class BankConnection(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_connections')
    aspsp_name = models.CharField(max_length=120)
    aspsp_country = models.CharField(max_length=2)
    state = models.CharField(max_length=64, unique=True)
    session_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=10, choices=BankConnectionStatus, default=BankConnectionStatus.PENDING)
    valid_until = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.aspsp_name} ({self.get_status_display()})'


class BankAccountLink(TimeStampedModel):
    connection = models.ForeignKey(BankConnection, on_delete=models.CASCADE, related_name='links')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='bank_links')
    uid = models.CharField(max_length=128)
    iban = models.CharField(max_length=34, blank=True)
    synced_until = models.DateField()
    bank_balance = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    bank_balance_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('account__created_at',)
        constraints = [models.UniqueConstraint(fields=('connection', 'uid'), name='unique_bank_account_per_connection')]

    def __str__(self):
        return f'{self.account} ← {self.iban or self.uid}'


class IgnoredBankTransaction(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ignored_bank_transactions')
    external_id = models.CharField(max_length=128)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'external_id'), name='unique_ignored_bank_transaction')]

    def __str__(self):
        return self.external_id


class PassThroughRule(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pass_through_rules')
    pattern = models.CharField(_('payer contains'), max_length=120)
    passed_on_amount = models.DecimalField(
        _('passed on to others'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    match_days = models.PositiveSmallIntegerField(default=30)

    def __str__(self):
        return f'{self.pattern}: {self.passed_on_amount} passed on'


class PendingPassThrough(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pending_pass_throughs')
    rule = models.ForeignKey(PassThroughRule, on_delete=models.CASCADE, related_name='pending')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    received_on = models.DateField()
    expires_on = models.DateField()

    class Meta:
        ordering = ('received_on',)
