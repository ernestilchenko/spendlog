from decimal import Decimal

from .choices import Currency

CURRENCY_SYMBOLS = {
    Currency.PLN: 'zł',
    Currency.EUR: '€',
    Currency.USD: '$',
    Currency.UAH: '₴',
    Currency.GBP: '£',
    Currency.CHF: 'CHF',
    Currency.CZK: 'Kč',
}


def format_money(amount, currency=Currency.PLN):
    value = Decimal(amount or 0).quantize(Decimal('0.01'))
    sign = '−' if value < 0 else ''
    integer, fraction = f'{abs(value):.2f}'.split('.')
    grouped = f'{int(integer):,}'.replace(',', ' ')
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    return f'{sign}{grouped},{fraction} {symbol}'
