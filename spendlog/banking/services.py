import hashlib
import json
import logging
import re
import secrets
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone

from spendlog.accounts.models import Account
from spendlog.accounts.services import assign_account
from spendlog.categories.services import categorize_expense, find_rule_category
from spendlog.categories.utils import normalize_merchant
from spendlog.core.choices import BankConnectionStatus, Currency, TransactionKind, TransactionSource
from spendlog.currencies.services import apply_conversion
from spendlog.transactions.models import Transaction

from .client import EnableBankingClient, EnableBankingError
from .models import BankAccountLink, BankConnection, IgnoredBankTransaction, PendingPassThrough

logger = logging.getLogger(__name__)

SYNC_OVERLAP_DAYS = 5
MATCH_WINDOW_DAYS = 2
INITIAL_HISTORY_DAYS = 90
BALANCE_TYPES = ('CLBD', 'ITBD', 'XPCD', 'CLAV', 'ITAV')
GENERIC_COUNTERPARTIES = {'', 'ecommerce'}
CARD_PAYMENT = re.compile(
    r'^\d{6}-+\d{4}\s+(?:[\d.,]+\s+)?\S+\s+\S+\s+(?P<merchant>.*?)\s+[A-Z]{3}\s+[\d.,]+\s+[A-Z]{3}\s+\d{4}-\d{2}-\d{2}'
)
CASH_WORDS = ('wypłata', 'wyplata', 'bankomat', 'atm', 'gotówk', 'gotowk')
FEE_WORDS = ('opłata', 'oplata', 'prowizja')
PHONE_TRANSFER_WORDS = ('przelew na telefon', 'blik phone', 'phone transfer', 'perekaz za nomerom')


class BankNotConfigured(Exception):
    pass


class UnknownConnectionState(Exception):
    pass


def bank_configured():
    return bool(settings.ENABLE_BANKING_APP_ID and settings.ENABLE_BANKING_KEY_PATH)


def require_configuration():
    if not bank_configured():
        raise BankNotConfigured


def get_client():
    return EnableBankingClient(settings.ENABLE_BANKING_APP_ID, Path(settings.ENABLE_BANKING_KEY_PATH).read_text())


def start_connection(user, redirect_url):
    require_configuration()
    state = secrets.token_urlsafe(24)
    valid_until = timezone.now() + timedelta(days=settings.ENABLE_BANKING_CONSENT_DAYS)
    url = get_client().start_auth(
        settings.ENABLE_BANKING_ASPSP,
        settings.ENABLE_BANKING_COUNTRY,
        redirect_url,
        state,
        valid_until,
    )
    BankConnection.objects.create(
        user=user,
        aspsp_name=settings.ENABLE_BANKING_ASPSP,
        aspsp_country=settings.ENABLE_BANKING_COUNTRY,
        state=state,
        valid_until=valid_until,
    )
    return url


def parse_datetime(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return parsed if timezone.is_aware(parsed) else timezone.make_aware(parsed)


def account_for(user, currency):
    account = user.accounts.filter(is_archived=False, currency=currency).first()
    return account or Account.objects.create(user=user, name=f'Bank {currency}', currency=currency)


def initial_sync_date(account):
    latest = account.transactions.order_by('-occurred_at').values_list('occurred_at', flat=True).first()
    if latest is not None:
        return timezone.localdate(latest)
    return timezone.localdate() - timedelta(days=INITIAL_HISTORY_DAYS)


def complete_connection(user, state, code):
    connection = user.bank_connections.filter(state=state, status=BankConnectionStatus.PENDING).first()
    if connection is None:
        raise UnknownConnectionState
    require_configuration()
    session = get_client().create_session(code)
    with db_transaction.atomic():
        user.bank_connections.filter(status=BankConnectionStatus.ACTIVE).update(status=BankConnectionStatus.EXPIRED)
        connection.session_id = session['session_id']
        connection.status = BankConnectionStatus.ACTIVE
        connection.valid_until = parse_datetime((session.get('access') or {}).get('valid_until')) or connection.valid_until
        connection.save()
        for item in session.get('accounts') or []:
            currency = item.get('currency') or Currency.PLN
            if currency not in Currency.values:
                continue
            account = account_for(user, currency)
            previous = BankAccountLink.objects.filter(account=account).order_by('-synced_until').first()
            BankAccountLink.objects.create(
                connection=connection,
                account=account,
                uid=item['uid'],
                iban=str((item.get('account_id') or {}).get('iban') or '')[:34],
                synced_until=previous.synced_until if previous else initial_sync_date(account),
            )
    return sync_connection(connection)


def sync_all():
    imported = 0
    for connection in BankConnection.objects.filter(status=BankConnectionStatus.ACTIVE).select_related('user'):
        try:
            imported += sync_connection(connection)
        except EnableBankingError:
            logger.exception('Bank sync failed for connection %s', connection.pk)
    return imported


def sync_connection(connection):
    now = timezone.now()
    if connection.valid_until and connection.valid_until <= now:
        connection.status = BankConnectionStatus.EXPIRED
        connection.save(update_fields=('status', 'updated_at'))
        return 0
    require_configuration()
    client = get_client()
    PendingPassThrough.objects.filter(user=connection.user, expires_on__lt=timezone.localdate()).delete()
    imported = 0
    try:
        for link in connection.links.select_related('account'):
            imported += sync_link(client, link)
    except EnableBankingError as exc:
        connection.last_error = str(exc)[:500]
        connection.save(update_fields=('last_error', 'updated_at'))
        raise
    connection.last_synced_at = now
    connection.last_error = ''
    connection.save(update_fields=('last_synced_at', 'last_error', 'updated_at'))
    return imported


def row_date(row):
    for key in ('transaction_date', 'booking_date', 'value_date'):
        if row.get(key):
            return date.fromisoformat(row[key][:10])
    return timezone.localdate()


def sync_link(client, link):
    rows = [
        row for row in client.transactions(link.uid, link.synced_until - timedelta(days=SYNC_OVERLAP_DAYS))
        if row.get('status', 'BOOK') == 'BOOK'
    ]
    rows.sort(key=row_date)
    imported = 0
    newest = link.synced_until
    for row in rows:
        imported += import_row(link.account, row)
        if row.get('booking_date'):
            newest = max(newest, date.fromisoformat(row['booking_date'][:10]))
    link.synced_until = newest
    update_bank_balance(client, link)
    link.save()
    return imported


def update_bank_balance(client, link):
    balances = {item.get('balance_type'): item for item in client.balances(link.uid)}
    for balance_type in BALANCE_TYPES:
        if balance_type in balances:
            link.bank_balance = Decimal(str(balances[balance_type]['balance_amount']['amount']))
            link.bank_balance_at = timezone.now()
            return


def remittance_text(row):
    info = row.get('remittance_information') or []
    return ' '.join(str(part) for part in info) if isinstance(info, list) else str(info)


def counterparty_name(row, kind):
    party = row.get('creditor' if kind == TransactionKind.EXPENSE else 'debtor') or {}
    return ' '.join(str(party.get('name') or '').split())


def external_id_for(row):
    for key in ('transaction_id', 'entry_reference'):
        if row.get(key):
            return f'eb:{row[key]}'[:128]
    fingerprint = json.dumps(
        [
            row.get('booking_date'),
            row.get('transaction_date'),
            row.get('transaction_amount'),
            row.get('credit_debit_indicator'),
            remittance_text(row),
            row.get('balance_after_transaction'),
        ],
        sort_keys=True,
        default=str,
    )
    return f'eb:h:{hashlib.sha256(fingerprint.encode()).hexdigest()[:40]}'


def merchant_for(text, counterparty):
    card = CARD_PAYMENT.match(text)
    if card:
        return card.group('merchant'), True
    if counterparty.lower() not in GENERIC_COUNTERPARTIES:
        return counterparty, False
    return text, False


def match_unlinked(account, kind, amount, currency, day):
    start = timezone.make_aware(datetime.combine(day - timedelta(days=MATCH_WINDOW_DAYS), time.min))
    end = timezone.make_aware(datetime.combine(day + timedelta(days=MATCH_WINDOW_DAYS + 1), time.min))
    return (
        account.transactions.filter(
            kind=kind,
            amount=amount,
            currency=currency,
            external_id='',
            occurred_at__gte=start,
            occurred_at__lt=end,
        )
        .order_by('occurred_at')
        .first()
    )


def category_named(user, name, kind):
    return user.categories.filter(name=name, kind=kind).first()


def expense_category(user, merchant, text, row, is_card, counterparty):
    code = json.dumps(row.get('bank_transaction_code') or {}, default=str, ensure_ascii=False).lower()
    low = f'{text} {code}'.lower()
    special = None
    if any(word in low for word in CASH_WORDS):
        special = 'Cash'
    elif not is_card and counterparty.lower() in GENERIC_COUNTERPARTIES and any(word in low for word in FEE_WORDS):
        special = 'Bank fees'
    elif any(word in low for word in PHONE_TRANSFER_WORDS):
        special = 'Transfers to people'
    category = category_named(user, special, TransactionKind.EXPENSE) if special else None
    if category is not None:
        return category
    rule = find_rule_category(user, f'{merchant} {text}')
    if rule is not None and rule.kind == TransactionKind.EXPENSE:
        return rule
    return categorize_expense(user, merchant)


def income_category(user, text):
    rule = find_rule_category(user, text)
    if rule is not None and rule.kind == TransactionKind.INCOME:
        return rule
    return category_named(user, 'Other income', TransactionKind.INCOME)


def apply_pass_through(user, text, amount, currency, day):
    normalized = normalize_merchant(text)
    for rule in user.pass_through_rules.all():
        if normalize_merchant(rule.pattern) in normalized and amount > rule.passed_on_amount:
            PendingPassThrough.objects.create(
                user=user,
                rule=rule,
                amount=rule.passed_on_amount,
                received_on=day,
                expires_on=day + timedelta(days=rule.match_days),
            )
            return amount - rule.passed_on_amount, f'Received {amount} {currency}, {rule.passed_on_amount} passed on'
    return amount, ''


def consume_pass_through(user, amount, day):
    pending = user.pending_pass_throughs.filter(amount=amount, received_on__lte=day, expires_on__gte=day).first()
    if pending is None:
        return False
    pending.delete()
    return True


def import_row(account, row):
    user = account.user
    external_id = external_id_for(row)
    if user.transactions.filter(external_id=external_id).exists():
        return 0
    if user.ignored_bank_transactions.filter(external_id=external_id).exists():
        return 0
    money = row.get('transaction_amount') or {}
    amount = abs(Decimal(str(money.get('amount', '0'))))
    currency = money.get('currency') or account.currency
    if not amount or currency not in Currency.values:
        return 0
    kind = TransactionKind.INCOME if row.get('credit_debit_indicator') == 'CRDT' else TransactionKind.EXPENSE
    day = row_date(row)
    text = ' '.join(remittance_text(row).split())
    counterparty = counterparty_name(row, kind)
    merchant, is_card = merchant_for(text, counterparty)
    existing = match_unlinked(account, kind, amount, currency, day)
    if existing is not None:
        existing.external_id = external_id
        existing.save(update_fields=('external_id', 'updated_at'))
        return 0
    if kind == TransactionKind.EXPENSE and not is_card and consume_pass_through(user, amount, day):
        IgnoredBankTransaction.objects.create(user=user, external_id=external_id, reason='Passed on part of income')
        return 0
    note = text
    if kind == TransactionKind.INCOME:
        amount, pass_note = apply_pass_through(user, f'{counterparty} {text}', amount, currency, day)
        note = f'{pass_note}. {text}' if pass_note else text
        category = income_category(user, f'{counterparty} {text}')
    else:
        category = expense_category(user, merchant, text, row, is_card, counterparty)
    transaction = Transaction(
        user=user,
        kind=kind,
        amount=amount,
        currency=currency,
        merchant=(merchant or text or account.name)[:160],
        category=category,
        occurred_at=timezone.make_aware(datetime.combine(day, time(12))),
        source=TransactionSource.BANK,
        external_id=external_id,
        note=note[:255],
    )
    apply_conversion(transaction)
    assign_account(transaction, account)
    transaction.save()
    return 1


def forget_bank_transaction(transaction):
    if transaction.external_id:
        IgnoredBankTransaction.objects.get_or_create(
            user=transaction.user,
            external_id=transaction.external_id,
            defaults={'reason': 'Deleted by the user'},
        )
