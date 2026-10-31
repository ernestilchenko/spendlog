from django.test import TestCase
from django.urls import reverse

from spendlog.categories.models import MerchantRule
from spendlog.core.testing import create_user, get_category


class RuleDeleteTests(TestCase):
    def test_deletes_rule(self):
        user = create_user()
        self.client.force_login(user)
        rule = MerchantRule.objects.create(user=user, pattern='lidl', category=get_category(user, 'Groceries'))
        response = self.client.post(reverse('categories:rule_delete', args=[rule.pk]))
        self.assertRedirects(response, reverse('categories:rule_list'))
        self.assertFalse(user.merchant_rules.exists())
