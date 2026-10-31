from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from spendlog.categories.models import MerchantRule
from spendlog.core.testing import create_user, get_category

SUGGEST = 'spendlog.categories.services.suggest_category_name'


class TransactionCreateTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.url = reverse('transactions:transaction_create')

    def payload(self, **overrides):
        data = {
            'kind': 'expense',
            'amount': '42.50',
            'currency': 'PLN',
            'merchant': 'Orlen',
            'category': '',
            'occurred_at': '2026-11-03T08:15',
            'note': '',
        }
        data.update(overrides)
        return data

    def test_creates_with_chosen_category(self):
        transport = get_category(self.user, 'Transport')
        response = self.client.post(self.url, self.payload(category=transport.pk))
        self.assertRedirects(response, reverse('transactions:transaction_list'))
        transaction = self.user.transactions.get()
        self.assertEqual(transaction.category, transport)
        self.assertEqual(str(transaction.amount), '42.50')

    @patch(SUGGEST, return_value='Transport')
    def test_auto_category_when_left_empty(self, suggest):
        self.client.post(self.url, self.payload())
        self.assertEqual(self.user.transactions.get().category.name, 'Transport')
        suggest.assert_called_once()

    def test_remember_merchant_creates_rule(self):
        transport = get_category(self.user, 'Transport')
        self.client.post(self.url, self.payload(category=transport.pk, remember_merchant='on', merchant='ORLEN Stacja 12'))
        rule = MerchantRule.objects.get(user=self.user)
        self.assertEqual(rule.pattern, 'orlen stacja 12')
        self.assertEqual(rule.category, transport)

    def test_category_must_match_kind(self):
        salary = get_category(self.user, 'Salary')
        response = self.client.post(self.url, self.payload(category=salary.pk))
        self.assertEqual(response.status_code, 200)
        self.assertIn('category', response.context['form'].errors)
        self.assertFalse(self.user.transactions.exists())

    def test_cannot_use_foreign_category(self):
        foreign = get_category(create_user('other@example.com'), 'Transport')
        response = self.client.post(self.url, self.payload(category=foreign.pk))
        self.assertIn('category', response.context['form'].errors)

    def test_rejects_non_positive_amount(self):
        response = self.client.post(self.url, self.payload(amount='0'))
        self.assertIn('amount', response.context['form'].errors)
