from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Sum
from django.utils.translation import gettext

from spendlog.core.choices import TransactionKind

RECENT_LIMIT = 8


@dataclass
class CategorySpending:
    name: str
    color: str
    spent: Decimal
    budget: Decimal | None
    share: int = 0

    @property
    def budget_percent(self):
        if not self.budget:
            return None
        return int(self.spent / self.budget * 100)

    @property
    def over_budget(self):
        return bool(self.budget) and self.spent > self.budget

    @property
    def left(self):
        return self.budget - self.spent if self.budget else None


def build_category_rows(user, expenses):
    spent_by_category = {
        row['category']: row['total'] for row in expenses.values('category').annotate(total=Sum('amount'))
    }
    rows = []
    for category in user.categories.filter(kind=TransactionKind.EXPENSE):
        spent = spent_by_category.get(category.pk, Decimal('0'))
        if spent or category.monthly_budget:
            rows.append(CategorySpending(category.display_name, category.color, spent, category.monthly_budget))
    uncategorized = spent_by_category.get(None)
    if uncategorized:
        rows.append(CategorySpending(gettext('Uncategorized'), '#cbd5e1', uncategorized, None))
    rows.sort(key=lambda row: row.spent, reverse=True)
    top = max((row.spent for row in rows), default=Decimal('0'))
    for row in rows:
        row.share = int(row.spent / top * 100) if top else 0
    return rows


def build_month_summary(user, month_start):
    transactions = user.transactions.in_month(month_start)
    expenses = transactions.expenses()
    income = transactions.incomes().total()
    expense = expenses.total()
    budgets = user.categories.filter(kind=TransactionKind.EXPENSE, monthly_budget__isnull=False)
    budget_total = budgets.aggregate(total=Sum('monthly_budget'))['total']
    budget_spent = expenses.filter(category__in=budgets).total()
    return {
        'income': income,
        'expense': expense,
        'balance': income - expense,
        'category_rows': build_category_rows(user, expenses),
        'budget_total': budget_total,
        'budget_spent': budget_spent,
        'budget_left': budget_total - budget_spent if budget_total else None,
        'recent_transactions': transactions.select_related('category')[:RECENT_LIMIT],
        'transaction_count': transactions.count(),
    }
