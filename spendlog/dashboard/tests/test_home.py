from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from spendlog.core.choices import TransactionKind
from spendlog.core.testing import create_transaction, create_user, get_category


class DashboardHomeTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.url = reverse('dashboard:home')

    def test_month_totals(self):
        groceries = get_category(self.user, 'Groceries')
        groceries.monthly_budget = Decimal('100.00')
        groceries.save()
        create_transaction(self.user, '30.00', category=groceries)
        create_transaction(self.user, '20.00', category=None)
        create_transaction(self.user, '5000.00', kind=TransactionKind.INCOME, category=get_category(self.user, 'Salary'))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['expense'], Decimal('50.00'))
        self.assertEqual(response.context['income'], Decimal('5000.00'))
        self.assertEqual(response.context['balance'], Decimal('4950.00'))
        self.assertEqual(response.context['budget_left'], Decimal('70.00'))
        names = [row.name for row in response.context['category_rows']]
        self.assertEqual(names, ['Groceries', 'Uncategorized'])

    def test_other_months_are_excluded(self):
        create_transaction(self.user, '99.00', occurred_at=timezone.now() - timedelta(days=62))
        response = self.client.get(self.url)
        self.assertEqual(response.context['expense'], Decimal('0'))

    def test_month_query_param(self):
        response = self.client.get(self.url, {'month': '2026-02'})
        self.assertEqual(response.context['month'].isoformat(), '2026-02-01')
        self.assertEqual(response.context['previous_month'].isoformat(), '2026-01-01')

    def test_other_users_data_is_hidden(self):
        create_transaction(create_user('other@example.com'), '77.00')
        response = self.client.get(self.url)
        self.assertEqual(response.context['transaction_count'], 0)
