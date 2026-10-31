from decimal import Decimal

from django.db import models
from django.db.models import Case, DecimalField, F, Sum, Value, When

from spendlog.core.choices import SavingsEntryKind
from spendlog.core.months import month_bounds

SIGNED_ORIGINAL_AMOUNT = Case(
    When(kind=SavingsEntryKind.WITHDRAWAL, then=-F('amount')),
    default=F('amount'),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)

SIGNED_AMOUNT = Case(
    When(kind=SavingsEntryKind.WITHDRAWAL, then=-F('amount_pln')),
    default=F('amount_pln'),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


class SavingsEntryQuerySet(models.QuerySet):
    def in_month(self, month_start):
        start, end = month_bounds(month_start)
        return self.filter(occurred_at__gte=start, occurred_at__lt=end)

    def balance(self):
        return self.aggregate(total=Sum(SIGNED_AMOUNT, default=Value(Decimal('0'))))['total']

    def balance_by_currency(self):
        rows = self.values('currency').annotate(total=Sum(SIGNED_ORIGINAL_AMOUNT)).order_by('currency')
        return {row['currency']: row['total'] for row in rows if row['total']}
