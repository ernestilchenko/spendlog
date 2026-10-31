from django.test import TestCase
from django.urls import reverse

from spendlog.core.choices import TransactionKind
from spendlog.core.testing import create_transaction, create_user, get_category


class TransactionListTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.url = reverse('transactions:transaction_list')

    def test_lists_only_own_transactions(self):
        own = create_transaction(self.user, merchant='Lidl')
        create_transaction(create_user('other@example.com'), merchant='Hidden')
        response = self.client.get(self.url)
        self.assertEqual(list(response.context['transactions']), [own])

    def test_filters_by_kind_and_category(self):
        groceries = get_category(self.user, 'Groceries')
        expense = create_transaction(self.user, category=groceries)
        create_transaction(self.user, kind=TransactionKind.INCOME, category=get_category(self.user, 'Salary'))
        uncategorized = create_transaction(self.user, category=None)
        response = self.client.get(self.url, {'kind': 'expense', 'category': groceries.pk})
        self.assertEqual(list(response.context['transactions']), [expense])
        response = self.client.get(self.url, {'category': 'none'})
        self.assertEqual(list(response.context['transactions']), [uncategorized])
