from django.db import models
from django.utils.translation import gettext_lazy as _


class TransactionKind(models.TextChoices):
    EXPENSE = 'expense', _('Expense')
    INCOME = 'income', _('Income')


class TransactionSource(models.TextChoices):
    MANUAL = 'manual', _('Manual')
    APPLE_PAY = 'apple_pay', 'Apple Pay'
    BANK = 'bank', _('Bank')


class Currency(models.TextChoices):
    PLN = 'PLN', 'PLN'
    EUR = 'EUR', 'EUR'
    USD = 'USD', 'USD'
    UAH = 'UAH', 'UAH'
    GBP = 'GBP', 'GBP'
    CHF = 'CHF', 'CHF'
    CZK = 'CZK', 'CZK'


class SavingsEntryKind(models.TextChoices):
    DEPOSIT = 'deposit', _('Deposit')
    WITHDRAWAL = 'withdrawal', _('Withdrawal')


class TokenPurpose(models.TextChoices):
    APPLE_PAY = 'apple_pay', 'Apple Pay'
    REPORTS = 'reports', 'Reports'


class BankConnectionStatus(models.TextChoices):
    PENDING = 'pending', _('Waiting for the bank')
    ACTIVE = 'active', _('Connected')
    EXPIRED = 'expired', _('Access expired')
    FAILED = 'failed', _('Failed')
