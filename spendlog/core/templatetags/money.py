from django import template

from spendlog.core.formatting import format_money

register = template.Library()


@register.filter
def money(amount):
    return format_money(amount)
