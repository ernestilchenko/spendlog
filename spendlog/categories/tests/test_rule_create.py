from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user, get_category


class RuleCreateTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.url = reverse('categories:rule_create')

    def test_creates_normalized_rule(self):
        groceries = get_category(self.user, 'Groceries')
        response = self.client.post(self.url, {'pattern': '  Biedronka   ', 'category': groceries.pk})
        self.assertRedirects(response, reverse('categories:rule_list'))
        self.assertEqual(self.user.merchant_rules.get().pattern, 'biedronka')

    def test_rejects_duplicate_pattern(self):
        groceries = get_category(self.user, 'Groceries')
        self.client.post(self.url, {'pattern': 'lidl', 'category': groceries.pk})
        response = self.client.post(self.url, {'pattern': 'LIDL', 'category': groceries.pk})
        self.assertIn('pattern', response.context['form'].errors)
