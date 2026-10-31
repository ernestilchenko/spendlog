from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from spendlog.core.testing import create_user
from spendlog.currencies.models import ExchangeRate
from spendlog.savings.models import SavingsGoal

FETCH = 'spendlog.currencies.nbp.fetch_nbp_rates'


class GoalCurrentValueTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.goal = SavingsGoal.objects.create(user=self.user, name='Savings')
        self.goal.entries.create(user=self.user, amount=Decimal('100'), currency='EUR', amount_pln=Decimal('400'))
        self.goal.entries.create(user=self.user, amount=Decimal('1000'), currency='PLN', amount_pln=Decimal('1000'))

    def test_foreign_savings_follow_todays_rate(self):
        with patch(FETCH, return_value={timezone.localdate(): Decimal('4.50')}):
            progress = self.client.get(reverse('savings:goal_detail', args=[self.goal.pk])).context['progress']
        self.assertEqual(progress.saved, Decimal('1450.00'))

    def test_falls_back_to_stored_value_without_any_rate(self):
        with patch(FETCH, return_value={}):
            progress = self.client.get(reverse('savings:goal_detail', args=[self.goal.pk])).context['progress']
        self.assertEqual(progress.saved, Decimal('1400'))

    def test_withdrawal_is_checked_per_currency(self):
        ExchangeRate.objects.create(currency='EUR', date=timezone.localdate() - timedelta(days=1), rate=Decimal('4'))
        url = reverse('savings:entry_create', args=[self.goal.pk])
        data = {
            'kind': 'withdrawal',
            'amount': '150',
            'currency': 'EUR',
            'account': '',
            'occurred_at': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
            'note': '',
        }
        with patch(FETCH, return_value={}):
            response = self.client.post(url, data)
            self.assertIn('amount', response.context['form'].errors)
            self.client.post(url, {**data, 'amount': '100'})
        self.assertNotIn('EUR', self.goal.entries.balance_by_currency())
