import secrets

from spendlog.categories.services import categorize_expense
from spendlog.core.choices import TransactionKind, TransactionSource
from spendlog.core.formatting import format_money
from spendlog.transactions.models import Transaction

from .messages import ApplePayMessages
from .models import ApiToken
from .utils import hash_token


def issue_token(user):
    raw_token = secrets.token_urlsafe(32)
    ApiToken.objects.update_or_create(user=user, defaults={'key_hash': hash_token(raw_token), 'last_used_at': None})
    return raw_token


def record_apple_pay_payment(user, amount, merchant, card):
    merchant = merchant.strip()[:160] or ApplePayMessages.DEFAULT_MERCHANT
    return Transaction.objects.create(
        user=user,
        kind=TransactionKind.EXPENSE,
        amount=amount,
        merchant=merchant,
        category=categorize_expense(user, merchant),
        source=TransactionSource.APPLE_PAY,
        card=card.strip()[:80],
    )


def build_payment_message(transaction):
    category = transaction.category.display_name if transaction.category else ApplePayMessages.UNCATEGORIZED
    return f'{transaction.merchant} · {format_money(transaction.amount)} → {category}'
