from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_transaction, create_user, get_category


class TransactionUpdateTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.transaction = create_transaction(self.user, merchant='Rossmann', category=get_category(self.user, 'Other'))
        self.url = reverse('transactions:transaction_update', args=[self.transaction.pk])

    def test_changes_category(self):
        health = get_category(self.user, 'Health & pharmacy')
        response = self.client.post(self.url, {
            'kind': 'expense',
            'amount': '10.00',
            'currency': 'PLN',
            'merchant': 'Rossmann',
            'category': health.pk,
            'occurred_at': '2026-11-03T10:00',
            'note': 'shampoo',
        })
        self.assertRedirects(response, reverse('transactions:transaction_list'))
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.category, health)
        self.assertEqual(self.transaction.note, 'shampoo')

    def test_foreign_transaction_is_404(self):
        foreign = create_transaction(create_user('other@example.com'))
        response = self.client.get(reverse('transactions:transaction_update', args=[foreign.pk]))
        self.assertEqual(response.status_code, 404)
