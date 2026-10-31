from django import template

from spendlog.core.choices import Currency
from spendlog.core.formatting import format_money

register = template.Library()


@register.filter
def money(amount, currency=Currency.PLN):
    return format_money(amount, currency or Currency.PLN)
