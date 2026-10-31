from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .messages import ApplePayMessages
from .models import ApiToken
from .services import build_payment_message, issue_token, record_apple_pay_payment
from .utils import get_user_by_token, parse_amount, read_payload

NEW_TOKEN_SESSION_KEY = 'new_api_token'


@csrf_exempt
@require_POST
def apple_pay_ingest(request):
    user = get_user_by_token(request)
    if user is None:
        return JsonResponse({'ok': False, 'message': ApplePayMessages.INVALID_TOKEN}, status=401)
    payload = read_payload(request)
    amount = parse_amount(payload.get('amount', ''))
    if amount is None:
        return JsonResponse({'ok': False, 'message': ApplePayMessages.INVALID_AMOUNT}, status=400)
    transaction = record_apple_pay_payment(
        user,
        amount,
        str(payload.get('merchant', '')),
        str(payload.get('card', '')),
    )
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
