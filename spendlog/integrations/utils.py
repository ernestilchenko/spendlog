import hashlib
import json
import re
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from spendlog.core.choices import Currency

from .models import ApiToken

AMOUNT_NOISE = re.compile(r'[^\d,.\-]')

CURRENCY_MARKERS = (
    ('PLN', Currency.PLN),
    ('zł', Currency.PLN),
    ('EUR', Currency.EUR),
    ('€', Currency.EUR),
    ('UAH', Currency.UAH),
    ('₴', Currency.UAH),
    ('GBP', Currency.GBP),
    ('£', Currency.GBP),
    ('CHF', Currency.CHF),
    ('CZK', Currency.CZK),
    ('Kč', Currency.CZK),
    ('USD', Currency.USD),
    ('$', Currency.USD),
)


def hash_token(raw_token):
    return hashlib.sha256(raw_token.encode()).hexdigest()


def get_user_by_token(request):
    scheme, _, raw_token = request.headers.get('Authorization', '').partition(' ')
    if scheme != 'Token' or not raw_token.strip():
        return None
    token = ApiToken.objects.select_related('user').filter(key_hash=hash_token(raw_token.strip())).first()
    if token is None or not token.user.is_active:
        return None
    token.last_used_at = timezone.now()
    token.save(update_fields=('last_used_at', 'updated_at'))
    return token.user


def read_payload(request):
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body or b'{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}
    return request.POST


def detect_currency(value, explicit=''):
    explicit = str(explicit or '').strip().upper()
    if explicit in Currency.values:
        return explicit
    text = str(value)
    for marker, currency in CURRENCY_MARKERS:
        if marker in text:
            return currency
    return Currency.PLN


def parse_amount(value):
    if isinstance(value, bool):
        return None
    text = AMOUNT_NOISE.sub('', str(value))
    if ',' in text and '.' in text:
        if text.rfind(',') > text.rfind('.'):
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '')
    else:
        text = text.replace(',', '.')
    try:
        amount = abs(Decimal(text)).quantize(Decimal('0.01'))
    except InvalidOperation:
        return None
    return amount if amount > 0 else None
