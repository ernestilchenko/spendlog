from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import CategoryForm, MerchantRuleForm
from .messages import CategoryMessages, RuleMessages


@login_required
@require_GET
def category_list(request):
    categories = sorted(
        request.user.categories.annotate(transaction_count=Count('transactions')),
        key=lambda category: (category.kind, category.display_name.casefold()),
    )
    return render(request, 'categories/category_list.html', {'categories': categories})


@login_required
@require_http_methods(['GET', 'POST'])
def category_create(request):
    form = CategoryForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        category = form.save(commit=False)
        category.user = request.user
        category.save()
        messages.success(request, CategoryMessages.CREATED)
        return redirect('categories:category_list')
    return render(request, 'categories/category_form.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def category_update(request, pk):
    category = get_object_or_404(request.user.categories, pk=pk)
    form = CategoryForm(request.POST or None, instance=category, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, CategoryMessages.UPDATED)
        return redirect('categories:category_list')
    return render(request, 'categories/category_form.html', {'form': form, 'category': category})


@login_required
@require_http_methods(['GET', 'POST'])
def category_delete(request, pk):
    category = get_object_or_404(request.user.categories, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, CategoryMessages.DELETED)
        return redirect('categories:category_list')
    return render(request, 'categories/category_confirm_delete.html', {'category': category})


@login_required
@require_GET
def rule_list(request):
    rules = request.user.merchant_rules.select_related('category')
    return render(request, 'categories/rule_list.html', {'rules': rules})


@login_required
@require_http_methods(['GET', 'POST'])
def rule_create(request):
    form = MerchantRuleForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        rule = form.save(commit=False)
        rule.user = request.user
        rule.save()
        messages.success(request, RuleMessages.CREATED)
        return redirect('categories:rule_list')
    return render(request, 'categories/rule_form.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def rule_delete(request, pk):
    rule = get_object_or_404(request.user.merchant_rules.select_related('category'), pk=pk)
    if request.method == 'POST':
        rule.delete()
        messages.success(request, RuleMessages.DELETED)
        return redirect('categories:rule_list')
    return render(request, 'categories/rule_confirm_delete.html', {'rule': rule})
