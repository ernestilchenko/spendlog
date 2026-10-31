from django.conf import settings
from django.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from spendlog.core.choices import TransactionKind
from spendlog.core.models import TimeStampedModel


class Category(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(_('name'), max_length=60)
    kind = models.CharField(_('type'), max_length=10, choices=TransactionKind, default=TransactionKind.EXPENSE)
    color = models.CharField(_('color'), max_length=7, default='#6366f1')
    monthly_budget = models.DecimalField(_('monthly budget'), max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ('kind', 'name')
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        constraints = [
            models.UniqueConstraint(fields=('user', 'name', 'kind'), name='unique_category_per_user'),
        ]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return gettext(self.name)


class MerchantRule(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='merchant_rules')
    pattern = models.CharField(_('merchant contains'), max_length=160)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='rules', verbose_name=_('category'))

    class Meta:
        ordering = ('pattern',)
        verbose_name = _('rule')
        verbose_name_plural = _('rules')
        constraints = [
            models.UniqueConstraint(fields=('user', 'pattern'), name='unique_rule_pattern_per_user'),
        ]

    def __str__(self):
        return f'{self.pattern} → {self.category}'
