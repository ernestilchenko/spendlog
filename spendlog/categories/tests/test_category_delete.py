from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_transaction, create_user, get_category


class CategoryDeleteTests(TestCase):
    def test_delete_keeps_transactions_uncategorized(self):
        user = create_user()
        self.client.force_login(user)
        groceries = get_category(user, 'Groceries')
        transaction = create_transaction(user, category=groceries)
        response = self.client.post(reverse('categories:category_delete', args=[groceries.pk]))
        self.assertRedirects(response, reverse('categories:category_list'))
        transaction.refresh_from_db()
        self.assertIsNone(transaction.category)
