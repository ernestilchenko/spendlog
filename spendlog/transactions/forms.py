from django import forms
from django.utils.translation import gettext_lazy as _

from .messages import TransactionMessages
from .models import Transaction

DATETIME_INPUT_FORMAT = '%Y-%m-%dT%H:%M'


class TransactionForm(forms.ModelForm):
    remember_merchant = forms.BooleanField(required=False, label=_('Always use this category for this merchant'))

    class Meta:
        model = Transaction
        fields = ('kind', 'amount', 'currency', 'account', 'merchant', 'category', 'occurred_at', 'note')
        widgets = {
            'occurred_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=DATETIME_INPUT_FORMAT),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'inputmode': 'decimal'}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = user.categories.all()
        self.fields['category'].empty_label = _('Auto')
        self.fields['account'].queryset = user.accounts.filter(is_archived=False)
        self.fields['account'].empty_label = _('Auto')
        self.fields['occurred_at'].input_formats = [DATETIME_INPUT_FORMAT]

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        kind = cleaned_data.get('kind')
        if category is not None and kind and category.kind != kind:
            self.add_error('category', TransactionMessages.CATEGORY_KIND_MISMATCH)
        return cleaned_data
