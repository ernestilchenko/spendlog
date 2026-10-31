import secrets

from spendlog.categories.services import categorize_expense
from django.utils import timezone

from spendlog.core.choices import Currency, TransactionKind, TransactionSource
from spendlog.core.formatting import format_money
from spendlog.currencies.services import apply_conversion
from spendlog.transactions.models import Transaction

from .messages import ApplePayMessages
from .models import ApiToken
from .utils import hash_token


def issue_token(user):
    raw_token = secrets.token_urlsafe(32)
    ApiToken.objects.update_or_create(user=user, defaults={'key_hash': hash_token(raw_token), 'last_used_at': None})
    return raw_token


def record_apple_pay_payment(user, amount, currency, merchant, card):
    merchant = merchant.strip()[:160] or ApplePayMessages.DEFAULT_MERCHANT
    transaction = Transaction(
        user=user,
        kind=TransactionKind.EXPENSE,
        amount=amount,
        currency=currency,
        merchant=merchant,
        source=TransactionSource.APPLE_PAY,
        card=card.strip()[:80],
        occurred_at=timezone.now(),
    )
    apply_conversion(transaction)
    transaction.category = categorize_expense(user, merchant)
    transaction.save()
    return transaction


def build_payment_message(transaction):
    category = transaction.category.display_name if transaction.category else ApplePayMessages.UNCATEGORIZED
    amount = format_money(transaction.amount, transaction.currency)
    if transaction.currency != Currency.PLN:
        amount = f'{amount} ≈ {format_money(transaction.amount_pln)}'
    return f'{transaction.merchant} · {amount} → {category}'
