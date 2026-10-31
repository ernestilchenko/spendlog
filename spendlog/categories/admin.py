from django.contrib import admin

from .models import Category, MerchantRule


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'user', 'monthly_budget')
    list_filter = ('kind',)
    search_fields = ('name',)


@admin.register(MerchantRule)
class MerchantRuleAdmin(admin.ModelAdmin):
    list_display = ('pattern', 'category', 'user')
    search_fields = ('pattern',)
