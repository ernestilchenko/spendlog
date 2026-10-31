from django.utils.translation import gettext_lazy as _


class ApplePayMessages:
    INVALID_TOKEN = _('Invalid or missing API token')
    INVALID_AMOUNT = _('Could not read the payment amount')
    UNCATEGORIZED = _('Uncategorized')
    DEFAULT_MERCHANT = 'Apple Pay'
    TOKEN_ISSUED = _('New token created. Copy it now: it will not be shown again')
