from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from spendlog.core.testing import create_user
from spendlog.savings.models import SavingsGoal


class EntryCreateTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.goal = SavingsGoal.objects.create(user=self.user, name='Apartment')
        self.url = reverse('savings:entry_create', args=[self.goal.pk])

    def payload(self, **overrides):
        data = {
            'kind': 'deposit',
            'amount': '1000',
            'currency': 'PLN',
            'account': '',
            'occurred_at': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
            'note': '',
        }
        data.update(overrides)
        return data

    def test_deposit(self):
        response = self.client.post(self.url, self.payload())
        self.assertRedirects(response, reverse('savings:goal_detail', args=[self.goal.pk]))
        self.assertEqual(self.goal.entries.balance(), Decimal('1000'))

    def test_deposit_in_euro(self):
        with patch('spendlog.currencies.nbp.fetch_nbp_rates', return_value={timezone.localdate(): Decimal('4.25')}):
            self.client.post(self.url, self.payload(amount='100', currency='EUR'))
        self.assertEqual(self.goal.entries.get().amount_pln, Decimal('425.00'))

    def test_withdrawal_reduces_balance(self):
        self.client.post(self.url, self.payload())
        self.client.post(self.url, self.payload(kind='withdrawal', amount='250'))
        self.assertEqual(self.goal.entries.balance(), Decimal('750'))

    def test_cannot_withdraw_more_than_saved(self):
        self.client.post(self.url, self.payload(amount='100'))
        response = self.client.post(self.url, self.payload(kind='withdrawal', amount='101'))
        self.assertIn('amount', response.context['form'].errors)
        self.assertEqual(self.goal.entries.count(), 1)

    def test_foreign_goal_is_404(self):
        goal = SavingsGoal.objects.create(user=create_user('other@example.com'), name='Hidden')
        response = self.client.post(reverse('savings:entry_create', args=[goal.pk]), self.payload())
        self.assertEqual(response.status_code, 404)
