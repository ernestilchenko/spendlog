from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_transaction, create_user


class TransactionDeleteTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)

    def test_get_shows_confirmation_and_keeps_transaction(self):
        transaction = create_transaction(self.user)
        response = self.client.get(reverse('transactions:transaction_delete', args=[transaction.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.transactions.exists())

    def test_post_deletes(self):
        transaction = create_transaction(self.user)
        response = self.client.post(reverse('transactions:transaction_delete', args=[transaction.pk]))
        self.assertRedirects(response, reverse('transactions:transaction_list'))
        self.assertFalse(self.user.transactions.exists())

    def test_foreign_transaction_is_404(self):
        foreign = create_transaction(create_user('other@example.com'))
        response = self.client.post(reverse('transactions:transaction_delete', args=[foreign.pk]))
        self.assertEqual(response.status_code, 404)
