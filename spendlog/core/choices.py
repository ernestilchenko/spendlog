from django.db import models
from django.utils.translation import gettext_lazy as _


class TransactionKind(models.TextChoices):
    EXPENSE = 'expense', _('Expense')
    INCOME = 'income', _('Income')


class TransactionSource(models.TextChoices):
    MANUAL = 'manual', _('Manual')
    APPLE_PAY = 'apple_pay', 'Apple Pay'
