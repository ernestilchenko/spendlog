import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from spendlog.currencies.messages import CurrencyMessages
from spendlog.currencies.services import ExchangeRateUnavailable

from .messages import ApplePayMessages
from .models import ApiToken
from .services import build_payment_message, issue_token, record_apple_pay_payment
from .utils import detect_currency, get_user_by_token, parse_amount, read_payload

NEW_TOKEN_SESSION_KEY = 'new_api_token'

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def apple_pay_ingest(request):
    user = get_user_by_token(request)
    if user is None:
        logger.warning('Apple Pay request with an invalid token')
        return JsonResponse({'ok': False, 'message': ApplePayMessages.INVALID_TOKEN}, status=401)
    payload = read_payload(request)
    raw_amount = payload.get('amount', '')
    amount = parse_amount(raw_amount)
    logger.info(
        'Apple Pay request: content_type=%s amount=%r merchant=%r card=%r',
        request.content_type,
        raw_amount,
        payload.get('merchant', ''),
        payload.get('card', ''),
    )
    if amount is None:
        return JsonResponse({'ok': False, 'message': ApplePayMessages.INVALID_AMOUNT}, status=400)
    try:
        transaction = record_apple_pay_payment(
            user,
            amount,
            detect_currency(raw_amount, payload.get('currency', '')),
            str(payload.get('merchant', '')),
            str(payload.get('card', '')),
        )
    except ExchangeRateUnavailable:
        return JsonResponse({'ok': False, 'message': CurrencyMessages.RATE_UNAVAILABLE}, status=503)
    return JsonResponse({'ok': True, 'id': transaction.pk, 'message': build_payment_message(transaction)}, status=201)


@login_required
@require_GET
def apple_pay_setup(request):
    context = {
        'token': ApiToken.objects.filter(user=request.user).first(),
        'new_token': request.session.pop(NEW_TOKEN_SESSION_KEY, None),
        'endpoint_url': request.build_absolute_uri(reverse('integrations:apple_pay_ingest')),
    }
    return render(request, 'integrations/apple_pay_setup.html', context)


@login_required
@require_POST
def token_regenerate(request):
    request.session[NEW_TOKEN_SESSION_KEY] = issue_token(request.user)
    messages.success(request, ApplePayMessages.TOKEN_ISSUED)
    return redirect('integrations:apple_pay_setup')
