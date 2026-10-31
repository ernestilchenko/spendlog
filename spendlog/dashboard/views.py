from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from spendlog.core.months import parse_month, shift_month

from .services import build_month_summary


@login_required
@require_GET
def home(request):
    month = parse_month(request.GET.get('month'))
    context = {
        'month': month,
        'previous_month': shift_month(month, -1),
        'next_month': shift_month(month, 1),
        **build_month_summary(request.user, month),
    }
    return render(request, 'dashboard/home.html', context)
