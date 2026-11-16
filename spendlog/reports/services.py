from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from spendlog.core.choices import TransactionKind
from spendlog.core.months import current_month
from spendlog.savings.services import active_goal_progress

from .messages import ReportMessages

TOP_CATEGORIES = 5


def money(value):
    return None if value is None else str(Decimal(value).quantize(Decimal('0.01')))


def day_start(day):
    return timezone.make_aware(datetime.combine(day, time.min))


def week_bounds(today):
    start = today - timedelta(days=today.weekday())
    return start, start + timedelta(days=7)


def in_range(queryset, start, end):
    return queryset.filter(occurred_at__gte=day_start(start), occurred_at__lt=day_start(end))


def top_categories(user, expenses):
    rows = expenses.values('category').annotate(total=Sum('amount_pln')).order_by('-total')[:TOP_CATEGORIES]
    names = {category.pk: category.display_name for category in user.categories.all()}
    return [
        {'name': names.get(row['category'], ReportMessages.UNCATEGORIZED), 'spent': money(row['total'])}
        for row in rows
    ]


def goal_rows(user, start, end):
    rows = []
    for progress in active_goal_progress(user):
        goal = progress.goal
        rows.append({
            'name': goal.name,
            'saved': money(progress.saved),
            'target': money(progress.target),
            'remaining': money(progress.remaining),
            'percent': progress.percent,
            'target_date': goal.target_date.isoformat() if goal.target_date else None,
            'monthly_needed': money(progress.monthly_needed),
            'saved_this_week': money(in_range(goal.entries.all(), start, end).balance()),
        })
    return rows


def build_weekly_summary(user, today=None):
    today = today or timezone.localdate()
    start, end = week_bounds(today)
    previous_start = start - timedelta(days=7)
    week = in_range(user.transactions.all(), start, end)
    expenses = week.expenses()
    month_expenses = user.transactions.in_month(current_month()).expenses()
    budgets = user.categories.filter(kind=TransactionKind.EXPENSE, monthly_budget__isnull=False)
    budget_total = budgets.aggregate(total=Sum('monthly_budget'))['total']
    budget_spent = month_expenses.filter(category__in=budgets).total()
    return {
        'currency': 'PLN',
        'week': {
            'start': start.isoformat(),
            'end': (end - timedelta(days=1)).isoformat(),
            'expense': money(expenses.total()),
            'income': money(week.incomes().total()),
            'saved': money(in_range(user.savings_entries.all(), start, end).balance()),
            'transactions': week.count(),
            'previous_expense': money(in_range(user.transactions.all(), previous_start, start).expenses().total()),
            'top_categories': top_categories(user, expenses),
        },
        'month': {
            'expense': money(month_expenses.total()),
            'budget_total': money(budget_total),
            'budget_left': money(budget_total - budget_spent) if budget_total else None,
        },
        'goals': goal_rows(user, start, end),
    }
