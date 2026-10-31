from django import forms

from .messages import CategoryMessages, RuleMessages
from .models import Category, MerchantRule
from .utils import normalize_merchant


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'kind', 'color', 'monthly_budget')
        widgets = {'color': forms.TextInput(attrs={'type': 'color'})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        duplicates = self.user.categories.filter(name=cleaned_data.get('name'), kind=cleaned_data.get('kind'))
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError(CategoryMessages.DUPLICATE)
        return cleaned_data


class MerchantRuleForm(forms.ModelForm):
    class Meta:
        model = MerchantRule
        fields = ('pattern', 'category')

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['category'].queryset = user.categories.all()

    def clean_pattern(self):
        pattern = normalize_merchant(self.cleaned_data['pattern'])
        if self.user.merchant_rules.filter(pattern=pattern).exists():
            raise forms.ValidationError(RuleMessages.DUPLICATE)
        return pattern
