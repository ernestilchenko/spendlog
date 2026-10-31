from django import forms

from spendlog.transactions.forms import DATETIME_INPUT_FORMAT

from .models import SavingsEntry, SavingsGoal


class SavingsGoalForm(forms.ModelForm):
    class Meta:
        model = SavingsGoal
        fields = ('name', 'target_amount', 'target_date', 'color', 'is_archived')
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
            'target_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'target_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'inputmode': 'decimal'}),
        }


class SavingsEntryForm(forms.ModelForm):
    class Meta:
        model = SavingsEntry
        fields = ('kind', 'amount', 'currency', 'occurred_at', 'note')
        widgets = {
            'occurred_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=DATETIME_INPUT_FORMAT),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'inputmode': 'decimal'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['occurred_at'].input_formats = [DATETIME_INPUT_FORMAT]
