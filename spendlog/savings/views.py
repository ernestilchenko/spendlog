from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from spendlog.core.choices import SavingsEntryKind
from spendlog.currencies.messages import CurrencyMessages
from spendlog.currencies.services import ExchangeRateUnavailable

from .forms import SavingsEntryForm, SavingsGoalForm
from .messages import SavingsMessages
from .services import NotEnoughSaved, goal_progress, save_entry


@login_required
@require_GET
def goal_list(request):
    progress = [goal_progress(goal) for goal in request.user.savings_goals.all()]
    total = sum((item.saved for item in progress), start=0)
    return render(request, 'savings/goal_list.html', {'progress_list': progress, 'total_saved': total})


@login_required
@require_http_methods(['GET', 'POST'])
def goal_create(request):
    form = SavingsGoalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()
        messages.success(request, SavingsMessages.GOAL_CREATED)
        return redirect('savings:goal_detail', pk=goal.pk)
    return render(request, 'savings/goal_form.html', {'form': form})


@login_required
@require_GET
def goal_detail(request, pk):
    goal = get_object_or_404(request.user.savings_goals, pk=pk)
    context = {'goal': goal, 'progress': goal_progress(goal), 'entries': goal.entries.all()}
    return render(request, 'savings/goal_detail.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def goal_update(request, pk):
    goal = get_object_or_404(request.user.savings_goals, pk=pk)
    form = SavingsGoalForm(request.POST or None, instance=goal)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, SavingsMessages.GOAL_UPDATED)
        return redirect('savings:goal_detail', pk=goal.pk)
    return render(request, 'savings/goal_form.html', {'form': form, 'goal': goal})


@login_required
@require_http_methods(['GET', 'POST'])
def goal_delete(request, pk):
    goal = get_object_or_404(request.user.savings_goals, pk=pk)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, SavingsMessages.GOAL_DELETED)
        return redirect('savings:goal_list')
    return render(request, 'savings/goal_confirm_delete.html', {'goal': goal})


@login_required
@require_http_methods(['GET', 'POST'])
def entry_create(request, pk):
    goal = get_object_or_404(request.user.savings_goals, pk=pk)
    initial = {
        'occurred_at': timezone.localtime().replace(second=0, microsecond=0),
        'kind': request.GET.get('kind', SavingsEntryKind.DEPOSIT),
    }
    form = SavingsEntryForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        try:
            save_entry(form, goal)
        except ExchangeRateUnavailable:
            form.add_error('currency', CurrencyMessages.RATE_UNAVAILABLE)
        except NotEnoughSaved:
            form.add_error('amount', SavingsMessages.NOT_ENOUGH)
        else:
            messages.success(request, SavingsMessages.ENTRY_CREATED)
            return redirect('savings:goal_detail', pk=goal.pk)
    return render(request, 'savings/entry_form.html', {'form': form, 'goal': goal})


@login_required
@require_http_methods(['GET', 'POST'])
def entry_delete(request, pk):
    entry = get_object_or_404(request.user.savings_entries.select_related('goal'), pk=pk)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, SavingsMessages.ENTRY_DELETED)
        return redirect('savings:goal_detail', pk=entry.goal_id)
    return render(request, 'savings/entry_confirm_delete.html', {'entry': entry})
