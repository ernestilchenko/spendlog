from django.utils.translation import gettext_lazy as _


class BankMessages:
    NOT_CONFIGURED = _('Bank sync is not configured on the server yet')
    BANK_ERROR = _('The bank connection failed: %(error)s')
    CONNECTED = _('Bank connected. %(count)s new transactions imported')
    CANCELLED = _('The bank did not grant access: %(error)s')
    UNKNOWN_STATE = _('This bank confirmation link is not valid anymore. Start the connection again')
    SYNCED = _('%(count)s new transactions imported')
    NO_CONNECTION = _('Connect the bank first')
