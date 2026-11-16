import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from spendlog.accounts.services import account_balance
from spendlog.core.choices import BankConnectionStatus

from .client import EnableBankingError
from .messages import BankMessages
from .services import (
    BankNotConfigured,
    UnknownConnectionState,
    bank_configured,
    complete_connection,
    start_connection,
    sync_connection,
)

logger = logging.getLogger(__name__)


@login_required
@require_GET
def bank_overview(request):
    connection = request.user.bank_connections.exclude(status=BankConnectionStatus.PENDING).first()
    links = []
    if connection is not None:
        for link in connection.links.select_related('account'):
            balance = account_balance(link.account)
            links.append({
                'link': link,
                'balance': balance,
                'difference': link.bank_balance - balance if link.bank_balance is not None else None,
            })
    context = {
        'configured': bank_configured(),
        'connection': connection,
        'links': links,
        'is_active': connection is not None and connection.status == BankConnectionStatus.ACTIVE,
    }
    return render(request, 'banking/overview.html', context)


@login_required
@require_POST
def bank_connect(request):
    try:
        url = start_connection(request.user, request.build_absolute_uri(reverse('banking:callback')))
    except BankNotConfigured:
        messages.error(request, BankMessages.NOT_CONFIGURED)
        return redirect('banking:overview')
    except EnableBankingError as exc:
        logger.warning('Bank connection start failed: %s', exc)
        messages.error(request, BankMessages.BANK_ERROR % {'error': exc})
        return redirect('banking:overview')
    return redirect(url)


@login_required
@require_GET
def bank_callback(request):
    error = request.GET.get('error')
    if error:
        messages.error(request, BankMessages.CANCELLED % {'error': request.GET.get('error_description') or error})
        return redirect('banking:overview')
    try:
        count = complete_connection(request.user, request.GET.get('state', ''), request.GET.get('code', ''))
    except UnknownConnectionState:
        messages.error(request, BankMessages.UNKNOWN_STATE)
    except BankNotConfigured:
        messages.error(request, BankMessages.NOT_CONFIGURED)
    except EnableBankingError as exc:
        logger.warning('Bank connection failed: %s', exc)
        messages.error(request, BankMessages.BANK_ERROR % {'error': exc})
    else:
        messages.success(request, BankMessages.CONNECTED % {'count': count})
    return redirect('banking:overview')


@login_required
@require_POST
def bank_sync(request):
    connection = request.user.bank_connections.filter(status=BankConnectionStatus.ACTIVE).first()
    if connection is None:
        messages.error(request, BankMessages.NO_CONNECTION)
        return redirect('banking:overview')
    try:
        count = sync_connection(connection)
    except BankNotConfigured:
        messages.error(request, BankMessages.NOT_CONFIGURED)
    except EnableBankingError as exc:
        messages.error(request, BankMessages.BANK_ERROR % {'error': exc})
    else:
        messages.success(request, BankMessages.SYNCED % {'count': count})
    return redirect('banking:overview')
