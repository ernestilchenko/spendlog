from django.http import JsonResponse
from django.utils import translation
from django.views.decorators.http import require_GET

from spendlog.core.choices import TokenPurpose
from spendlog.integrations.utils import get_user_by_token

from .messages import ReportMessages
from .services import build_weekly_summary


@require_GET
def weekly_summary(request):
    user = get_user_by_token(request, TokenPurpose.REPORTS)
    if user is None:
        return JsonResponse({'ok': False, 'message': ReportMessages.INVALID_TOKEN}, status=401)
    with translation.override('en'):
        summary = build_weekly_summary(user)
    return JsonResponse({'ok': True, **summary})
