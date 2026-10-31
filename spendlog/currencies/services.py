from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.utils import timezone

from spendlog.core.choices import Currency

from . import nbp
from .models import ExchangeRate

CENT = Decimal('0.01')


class ExchangeRateUnavailable(Exception):
    pass


def latest_stored_rate(currency, on_date, earliest=None):
    rates = ExchangeRate.objects.filter(currency=currency, date__lte=on_date)
    if earliest is not None:
        rates = rates.filter(date__gte=earliest)
    return rates.order_by('-date').first()


def get_rate(currency, on_date):
    if currency == Currency.PLN:
        return Decimal('1')
    on_date = min(on_date, timezone.localdate())
    earliest = on_date - timedelta(days=settings.NBP_LOOKBACK_DAYS)
    stored = latest_stored_rate(currency, on_date, earliest)
    if stored is not None and stored.date == on_date:
        return stored.rate
    fetched = nbp.fetch_nbp_rates(currency, earliest, on_date)
    for rate_date, rate in fetched.items():
        ExchangeRate.objects.update_or_create(currency=currency, date=rate_date, defaults={'rate': rate})
    stored = latest_stored_rate(currency, on_date, earliest) or latest_stored_rate(currency, on_date)
    if stored is None:
        raise ExchangeRateUnavailable(currency)
    return stored.rate


def apply_conversion(record):
    record.exchange_rate = get_rate(record.currency, timezone.localdate(record.occurred_at))
    record.amount_pln = (record.amount * record.exchange_rate).quantize(CENT, rounding=ROUND_HALF_UP)
    return record
