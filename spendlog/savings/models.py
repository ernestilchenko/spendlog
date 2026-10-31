from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from spendlog.accounts.models import Account
from spendlog.core.choices import Currency, SavingsEntryKind
from spendlog.core.models import TimeStampedModel

from .managers import SavingsEntryQuerySet


class SavingsGoal(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(_('name'), max_length=80)
    target_amount = models.DecimalField(
        _('target in PLN'),
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    target_date = models.DateField(_('target date'), null=True, blank=True)
    color = models.CharField(_('color'), max_length=7, default='#c96442')
    is_archived = models.BooleanField(_('archived'), default=False)

    class Meta:
        ordering = ('is_archived', 'created_at')
        verbose_name = _('savings goal')
        verbose_name_plural = _('savings goals')

    def __str__(self):
        return self.name


class SavingsEntry(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='savings_entries')
    goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name='entries', verbose_name=_('goal'))
    kind = models.CharField(_('type'), max_length=10, choices=SavingsEntryKind, default=SavingsEntryKind.DEPOSIT)
    amount = models.DecimalField(_('amount'), max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(_('currency'), max_length=3, choices=Currency, default=Currency.PLN)
    amount_pln = models.DecimalField(_('amount in PLN'), max_digits=14, decimal_places=2)
    exchange_rate = models.DecimalField(_('exchange rate'), max_digits=12, decimal_places=6, default=Decimal('1'))
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='savings_entries',
        verbose_name=_('account'),
    )
    account_amount = models.DecimalField(_('amount in account currency'), max_digits=14, decimal_places=2, null=True, blank=True)
    occurred_at = models.DateTimeField(_('date'), default=timezone.now)
    note = models.CharField(_('note'), max_length=255, blank=True)

    objects = SavingsEntryQuerySet.as_manager()

    class Meta:
        ordering = ('-occurred_at', '-id')
        verbose_name = _('savings entry')
        verbose_name_plural = _('savings entries')

    def __str__(self):
        return f'{self.goal} {self.get_kind_display()} {self.amount}'

    @property
    def is_withdrawal(self):
        return self.kind == SavingsEntryKind.WITHDRAWAL

    @property
    def is_foreign(self):
        return self.currency != Currency.PLN
