from django.db import models
from django.utils.translation import gettext_lazy as _

from spendlog.core.choices import Currency


class ExchangeRate(models.Model):
    currency = models.CharField(_('currency'), max_length=3, choices=Currency)
    date = models.DateField(_('date'))
    rate = models.DecimalField(_('rate to PLN'), max_digits=12, decimal_places=6)

    class Meta:
        ordering = ('-date',)
        constraints = [
            models.UniqueConstraint(fields=('currency', 'date'), name='unique_rate_per_currency_day'),
        ]

    def __str__(self):
        return f'{self.currency} {self.date}: {self.rate}'
