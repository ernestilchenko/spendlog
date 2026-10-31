from spendlog.core.choices import TransactionKind

UNCATEGORIZED = 'none'


def filter_transactions(queryset, params):
    kind = params.get('kind')
    if kind in TransactionKind.values:
        queryset = queryset.filter(kind=kind)
    category = params.get('category')
    if category == UNCATEGORIZED:
        queryset = queryset.filter(category__isnull=True)
    elif category and category.isdigit():
        queryset = queryset.filter(category_id=int(category))
    return queryset
