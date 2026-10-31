from decimal import Decimal

from django.db import models
from django.db.models import Sum

from spendlog.core.choices import TransactionKind
from spendlog.core.months import month_bounds


class TransactionQuerySet(models.QuerySet):
    def in_month(self, month_start):
        start, end = month_bounds(month_start)
        return self.filter(occurred_at__gte=start, occurred_at__lt=end)

    def expenses(self):
        return self.filter(kind=TransactionKind.EXPENSE)

    def incomes(self):
        return self.filter(kind=TransactionKind.INCOME)

    def total(self):
        return self.aggregate(total=Sum('amount_pln'))['total'] or Decimal('0')
