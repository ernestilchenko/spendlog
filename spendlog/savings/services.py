from dataclasses import dataclass
from decimal import ROUND_UP, Decimal

from django.utils import timezone

from spendlog.currencies.services import apply_conversion

CENT = Decimal('0.01')


class NotEnoughSaved(Exception):
    pass


@dataclass
class GoalProgress:
    goal: object
    saved: Decimal

    @property
    def target(self):
        return self.goal.target_amount

    @property
    def percent(self):
        if not self.target:
            return None
        return min(int(self.saved / self.target * 100), 100)

    @property
    def remaining(self):
        if not self.target:
            return None
        return max(self.target - self.saved, Decimal('0'))

    @property
    def months_left(self):
        if self.goal.target_date is None:
            return None
        today = timezone.localdate()
        months = (self.goal.target_date.year - today.year) * 12 + self.goal.target_date.month - today.month
        return max(months, 1)

    @property
    def monthly_needed(self):
        if not self.remaining or self.months_left is None:
            return None
        return (self.remaining / self.months_left).quantize(CENT, rounding=ROUND_UP)

    @property
    def is_reached(self):
        return bool(self.target) and self.saved >= self.target


def goal_progress(goal):
    return GoalProgress(goal, goal.entries.balance())


def active_goal_progress(user):
    return [goal_progress(goal) for goal in user.savings_goals.filter(is_archived=False)]


def save_entry(form, goal):
    entry = form.save(commit=False)
    entry.user = goal.user
    entry.goal = goal
    apply_conversion(entry)
    if entry.is_withdrawal and entry.amount_pln > goal.entries.balance():
        raise NotEnoughSaved
    entry.save()
    return entry


def month_savings(user, month_start):
    return user.savings_entries.in_month(month_start).balance()
