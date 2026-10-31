from django.utils.translation import gettext_lazy as _


class TransactionMessages:
    CREATED = _('Transaction added')
    UPDATED = _('Transaction saved')
    DELETED = _('Transaction deleted')
    CATEGORY_KIND_MISMATCH = _('This category does not match the transaction type')
