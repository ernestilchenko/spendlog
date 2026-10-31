from django import forms

from spendlog.transactions.forms import DATETIME_INPUT_FORMAT

from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('name', 'currency', 'opening_balance', 'opening_date', 'color', 'is_archived')
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
            'opening_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=DATETIME_INPUT_FORMAT),
            'opening_balance': forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['opening_date'].input_formats = [DATETIME_INPUT_FORMAT]
