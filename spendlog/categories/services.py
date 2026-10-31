from django.utils.translation import gettext_noop

from spendlog.core.choices import TransactionKind

from .ai import suggest_category_name
from .models import Category, MerchantRule
from .utils import normalize_merchant

FALLBACK_CATEGORY_NAME = gettext_noop('Other')

DEFAULT_CATEGORIES = (
    (gettext_noop('Groceries'), TransactionKind.EXPENSE, '#16a34a'),
    (gettext_noop('Cafes & restaurants'), TransactionKind.EXPENSE, '#f97316'),
    (gettext_noop('Transport'), TransactionKind.EXPENSE, '#0ea5e9'),
    (gettext_noop('Housing & bills'), TransactionKind.EXPENSE, '#6366f1'),
    (gettext_noop('Phone & subscriptions'), TransactionKind.EXPENSE, '#8b5cf6'),
    (gettext_noop('Health & pharmacy'), TransactionKind.EXPENSE, '#ef4444'),
    (gettext_noop('Clothes & shoes'), TransactionKind.EXPENSE, '#ec4899'),
    (gettext_noop('Home'), TransactionKind.EXPENSE, '#14b8a6'),
    (gettext_noop('Entertainment'), TransactionKind.EXPENSE, '#eab308'),
    (gettext_noop('Online shopping'), TransactionKind.EXPENSE, '#64748b'),
    (FALLBACK_CATEGORY_NAME, TransactionKind.EXPENSE, '#94a3b8'),
    (gettext_noop('Salary'), TransactionKind.INCOME, '#16a34a'),
    (gettext_noop('Side income'), TransactionKind.INCOME, '#22c55e'),
    (gettext_noop('Bonus'), TransactionKind.INCOME, '#84cc16'),
    (gettext_noop('Other income'), TransactionKind.INCOME, '#94a3b8'),
)


def create_default_categories(user):
    Category.objects.bulk_create(
        [Category(user=user, name=name, kind=kind, color=color) for name, kind, color in DEFAULT_CATEGORIES],
        ignore_conflicts=True,
    )


def find_rule_category(user, merchant):
    normalized = normalize_merchant(merchant)
    if not normalized:
        return None
    matches = [rule for rule in user.merchant_rules.select_related('category') if rule.pattern in normalized]
    if not matches:
        return None
    return max(matches, key=lambda rule: len(rule.pattern)).category


def remember_merchant(user, merchant, category):
    pattern = normalize_merchant(merchant)
    if pattern:
        MerchantRule.objects.update_or_create(user=user, pattern=pattern, defaults={'category': category})


def fallback_category(user):
    return user.categories.filter(name=FALLBACK_CATEGORY_NAME, kind=TransactionKind.EXPENSE).first()


def categorize_expense(user, merchant):
    category = find_rule_category(user, merchant)
    if category is not None:
        return category
    categories = {category.name: category for category in user.categories.filter(kind=TransactionKind.EXPENSE)}
    suggested_name = suggest_category_name(merchant, list(categories))
    if suggested_name is not None:
        category = categories[suggested_name]
        remember_merchant(user, merchant, category)
        return category
    return fallback_category(user)
