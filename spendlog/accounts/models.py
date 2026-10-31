from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from spendlog.core.choices import Currency
from spendlog.core.models import TimeStampedModel


class Account(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(_('name'), max_length=60)
    currency = models.CharField(_('currency'), max_length=3, choices=Currency, default=Currency.PLN)
    opening_balance = models.DecimalField(_('balance at start'), max_digits=14, decimal_places=2, default=Decimal('0'))
    opening_date = models.DateTimeField(_('balance date'), default=timezone.now)
    color = models.CharField(_('color'), max_length=7, default='#6b6a65')
    is_archived = models.BooleanField(_('archived'), default=False)

    class Meta:
        ordering = ('is_archived', 'created_at')
        verbose_name = _('account')
        verbose_name_plural = _('accounts')

    def __str__(self):
        return f'{self.name} · {self.currency}'
