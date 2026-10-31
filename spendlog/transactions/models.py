from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from spendlog.categories.models import Category
from spendlog.core.choices import Currency, TransactionKind, TransactionSource
from spendlog.core.models import TimeStampedModel

from .managers import TransactionQuerySet


class Transaction(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    kind = models.CharField(_('type'), max_length=10, choices=TransactionKind, default=TransactionKind.EXPENSE)
    amount = models.DecimalField(_('amount'), max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(_('currency'), max_length=3, choices=Currency, default=Currency.PLN)
    amount_pln = models.DecimalField(_('amount in PLN'), max_digits=12, decimal_places=2)
    exchange_rate = models.DecimalField(_('exchange rate'), max_digits=12, decimal_places=6, default=Decimal('1'))
    merchant = models.CharField(_('merchant'), max_length=160, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('category'),
    )
    occurred_at = models.DateTimeField(_('date'), default=timezone.now)
    source = models.CharField(_('source'), max_length=20, choices=TransactionSource, default=TransactionSource.MANUAL)
    card = models.CharField(_('card'), max_length=80, blank=True)
    note = models.CharField(_('note'), max_length=255, blank=True)

    objects = TransactionQuerySet.as_manager()

    class Meta:
        ordering = ('-occurred_at', '-id')
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        indexes = [models.Index(fields=('user', 'occurred_at'))]

    def __str__(self):
        return f'{self.merchant or self.get_kind_display()} {self.amount}'

    @property
    def is_expense(self):
        return self.kind == TransactionKind.EXPENSE

    @property
    def is_foreign(self):
        return self.currency != Currency.PLN
