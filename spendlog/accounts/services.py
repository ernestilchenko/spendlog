from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Case, DecimalField, F, Sum, Value, When
from django.utils import timezone

from spendlog.core.choices import Currency, SavingsEntryKind, TransactionKind
from spendlog.currencies.services import ExchangeRateUnavailable, get_rate

CENT = Decimal('0.01')
ZERO = Decimal('0')
MONEY = DecimalField(max_digits=14, decimal_places=2)


@dataclass
class AccountBalance:
    account: object
    balance: Decimal
    balance_pln: Decimal | None


def default_account(user, currency):
    accounts = user.accounts.filter(is_archived=False)
    return accounts.filter(currency=currency).first() or accounts.filter(currency=Currency.PLN).first()


def amount_in_account_currency(record, account):
    if account is None:
        return None
    if record.currency == account.currency:
        return record.amount
    rate = get_rate(account.currency, timezone.localdate(record.occurred_at))
    return (record.amount_pln / rate).quantize(CENT, rounding=ROUND_HALF_UP)


def assign_account(record, account):
    record.account = account
    record.account_amount = amount_in_account_currency(record, account)
    return record


def account_balance(account):
    transactions = account.transactions.filter(occurred_at__gte=account.opening_date).aggregate(
        total=Sum(
            Case(
                When(kind=TransactionKind.EXPENSE, then=-F('account_amount')),
                default=F('account_amount'),
                output_field=MONEY,
            ),
            default=Value(ZERO),
        )
    )['total']
    savings = account.savings_entries.filter(occurred_at__gte=account.opening_date).aggregate(
        total=Sum(
            Case(
                When(kind=SavingsEntryKind.WITHDRAWAL, then=F('account_amount')),
                default=-F('account_amount'),
                output_field=MONEY,
            ),
            default=Value(ZERO),
        )
    )['total']
    return account.opening_balance + transactions + savings


def balance_in_pln(balance, currency):
    try:
        rate = get_rate(currency, timezone.localdate())
    except ExchangeRateUnavailable:
        return None
    return (balance * rate).quantize(CENT, rounding=ROUND_HALF_UP)


def account_balances(user, include_archived=False):
    accounts = user.accounts.all() if include_archived else user.accounts.filter(is_archived=False)
    balances = []
    for account in accounts:
        balance = account_balance(account)
        balances.append(AccountBalance(account, balance, balance_in_pln(balance, account.currency)))
    return balances


def total_in_pln(balances):
    return sum((item.balance_pln or ZERO for item in balances), start=ZERO)
