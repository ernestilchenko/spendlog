from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from spendlog.core.choices import TransactionKind
from spendlog.core.months import parse_month, shift_month
from spendlog.currencies.messages import CurrencyMessages
from spendlog.currencies.services import ExchangeRateUnavailable

from .forms import TransactionForm
from .messages import TransactionMessages
from .services import save_transaction
from .utils import UNCATEGORIZED, filter_transactions


@login_required
@require_GET
def transaction_list(request):
    month = parse_month(request.GET.get('month'))
    month_transactions = request.user.transactions.in_month(month)
    transactions = filter_transactions(month_transactions, request.GET).select_related('category', 'account')
    context = {
        'transactions': transactions,
        'month': month,
        'previous_month': shift_month(month, -1),
        'next_month': shift_month(month, 1),
        'expense_total': transactions.expenses().total(),
        'income_total': transactions.incomes().total(),
        'categories': request.user.categories.all(),
        'kinds': TransactionKind.choices,
        'selected_kind': request.GET.get('kind', ''),
        'selected_category': request.GET.get('category', ''),
        'uncategorized': UNCATEGORIZED,
    }
    return render(request, 'transactions/transaction_list.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def transaction_create(request):
    initial = {
        'occurred_at': timezone.localtime().replace(second=0, microsecond=0),
        'kind': request.GET.get('kind', TransactionKind.EXPENSE),
    }
    form = TransactionForm(request.POST or None, user=request.user, initial=initial)
    if request.method == 'POST' and form.is_valid():
        try:
            save_transaction(form, request.user)
        except ExchangeRateUnavailable:
            form.add_error('currency', CurrencyMessages.RATE_UNAVAILABLE)
        else:
            messages.success(request, TransactionMessages.CREATED)
            return redirect('transactions:transaction_list')
    return render(request, 'transactions/transaction_form.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def transaction_update(request, pk):
    transaction = get_object_or_404(request.user.transactions, pk=pk)
    form = TransactionForm(request.POST or None, instance=transaction, user=request.user)
    if request.method == 'POST' and form.is_valid():
        try:
            save_transaction(form, request.user)
        except ExchangeRateUnavailable:
            form.add_error('currency', CurrencyMessages.RATE_UNAVAILABLE)
        else:
            messages.success(request, TransactionMessages.UPDATED)
            return redirect('transactions:transaction_list')
    return render(request, 'transactions/transaction_form.html', {'form': form, 'transaction': transaction})


@login_required
@require_http_methods(['GET', 'POST'])
def transaction_delete(request, pk):
    transaction = get_object_or_404(request.user.transactions.select_related('category'), pk=pk)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, TransactionMessages.DELETED)
        return redirect('transactions:transaction_list')
    return render(request, 'transactions/transaction_confirm_delete.html', {'transaction': transaction})
