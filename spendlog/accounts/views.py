from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from .forms import AccountForm
from .messages import AccountMessages
from .services import account_balances, total_in_pln


@login_required
@require_GET
def account_list(request):
    balances = account_balances(request.user, include_archived=True)
    active = [item for item in balances if not item.account.is_archived]
    return render(request, 'accounts/account_list.html', {'balances': balances, 'total_pln': total_in_pln(active)})


@login_required
@require_http_methods(['GET', 'POST'])
def account_create(request):
    initial = {'opening_date': timezone.localtime().replace(second=0, microsecond=0)}
    form = AccountForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        account = form.save(commit=False)
        account.user = request.user
        account.save()
        messages.success(request, AccountMessages.CREATED)
        return redirect('accounts:account_list')
    return render(request, 'accounts/account_form.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def account_update(request, pk):
    account = get_object_or_404(request.user.accounts, pk=pk)
    form = AccountForm(request.POST or None, instance=account)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, AccountMessages.UPDATED)
        return redirect('accounts:account_list')
    return render(request, 'accounts/account_form.html', {'form': form, 'account': account})


@login_required
@require_http_methods(['GET', 'POST'])
def account_delete(request, pk):
    account = get_object_or_404(request.user.accounts, pk=pk)
    if request.method == 'POST':
        account.delete()
        messages.success(request, AccountMessages.DELETED)
        return redirect('accounts:account_list')
    return render(request, 'accounts/account_confirm_delete.html', {'account': account})
