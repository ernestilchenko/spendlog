from decimal import Decimal

from django.conf import settings


def format_money(amount):
    value = Decimal(amount or 0).quantize(Decimal('0.01'))
    sign = '−' if value < 0 else ''
    integer, fraction = f'{abs(value):.2f}'.split('.')
    grouped = f'{int(integer):,}'.replace(',', ' ')
    return f'{sign}{grouped},{fraction} {settings.CURRENCY_SYMBOL}'
