from spendlog.categories.services import categorize_expense, remember_merchant
from spendlog.core.choices import TransactionKind
from spendlog.currencies.services import apply_conversion


def save_transaction(form, user):
    transaction = form.save(commit=False)
    transaction.user = user
    apply_conversion(transaction)
    if transaction.category is None and transaction.kind == TransactionKind.EXPENSE and transaction.merchant:
        transaction.category = categorize_expense(user, transaction.merchant)
    transaction.save()
    if form.cleaned_data.get('remember_merchant') and transaction.category and transaction.merchant:
        remember_merchant(user, transaction.merchant, transaction.category)
    return transaction
