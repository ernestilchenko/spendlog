from django.test import TestCase
from django.urls import reverse

from spendlog.categories.models import MerchantRule
from spendlog.core.testing import create_user, get_category


class RuleListTests(TestCase):
    def test_lists_own_rules(self):
        user = create_user()
        other = create_user('other@example.com')
        MerchantRule.objects.create(user=user, pattern='zabka', category=get_category(user, 'Groceries'))
        MerchantRule.objects.create(user=other, pattern='hidden', category=get_category(other, 'Groceries'))
        self.client.force_login(user)
        response = self.client.get(reverse('categories:rule_list'))
        self.assertEqual([rule.pattern for rule in response.context['rules']], ['zabka'])
