from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from spendlog.core.choices import TransactionKind
from spendlog.transactions.models import Transaction

PASSWORD = 'spendlog-pass-123'


def create_user(email='owner@example.com'):
    return get_user_model().objects.create_user(email=email, password=PASSWORD)


def get_category(user, name):
    return user.categories.get(name=name)


def create_transaction(user, amount='10.00', kind=TransactionKind.EXPENSE, category=None, merchant='Shop', occurred_at=None):
    return Transaction.objects.create(
        user=user,
        kind=kind,
        amount=Decimal(amount),
        merchant=merchant,
        category=category,
        occurred_at=occurred_at or timezone.now(),
    )
