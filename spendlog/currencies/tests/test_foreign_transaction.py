from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from spendlog.core.testing import create_user, get_category
from spendlog.currencies.models import ExchangeRate

FETCH = 'spendlog.currencies.nbp.fetch_nbp_rates'


class ForeignCurrencyTransactionTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.url = reverse('transactions:transaction_create')
        self.today = timezone.localdate()

    def payload(self, **overrides):
        data = {
            'kind': 'expense',
            'amount': '12.50',
            'currency': 'EUR',
            'account': '',
            'merchant': 'Cafe in Berlin',
            'category': get_category(self.user, 'Cafes & restaurants').pk,
            'occurred_at': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
            'note': '',
        }
        data.update(overrides)
        return data

    def test_converts_with_nbp_rate_and_caches_it(self):
        with patch(FETCH, return_value={self.today: Decimal('4.2731')}) as fetch:
            self.client.post(self.url, self.payload())
            self.client.post(self.url, self.payload(amount='10'))
        first, second = self.user.transactions.order_by('id')
        self.assertEqual(first.currency, 'EUR')
        self.assertEqual(first.amount, Decimal('12.50'))
        self.assertEqual(first.amount_pln, Decimal('53.41'))
        self.assertEqual(second.amount_pln, Decimal('42.73'))
        fetch.assert_called_once()
        self.assertTrue(ExchangeRate.objects.filter(currency='EUR', date=self.today).exists())

    def test_weekend_uses_last_published_rate(self):
        friday = self.today - timedelta(days=(self.today.weekday() - 4) % 7 or 7)
        with patch(FETCH, return_value={friday: Decimal('4.0000')}):
            self.client.post(self.url, self.payload(amount='5'))
        self.assertEqual(self.user.transactions.get().amount_pln, Decimal('20.00'))

    def test_shows_error_when_rate_is_unavailable(self):
        with patch(FETCH, return_value={}):
            response = self.client.post(self.url, self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertIn('currency', response.context['form'].errors)
        self.assertFalse(self.user.transactions.exists())

    def test_falls_back_to_older_stored_rate_when_nbp_is_down(self):
        ExchangeRate.objects.create(currency='EUR', date=date(2025, 1, 2), rate=Decimal('4.3000'))
        with patch(FETCH, return_value={}):
            self.client.post(self.url, self.payload(amount='10'))
        self.assertEqual(self.user.transactions.get().amount_pln, Decimal('43.00'))

    def test_pln_never_calls_nbp(self):
        with patch(FETCH) as fetch:
            self.client.post(self.url, self.payload(currency='PLN'))
        fetch.assert_not_called()
        self.assertEqual(self.user.transactions.get().amount_pln, Decimal('12.50'))

    def test_month_totals_use_pln(self):
        with patch(FETCH, return_value={self.today: Decimal('4')}):
            self.client.post(self.url, self.payload(amount='10'))
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.context['expense'], Decimal('40.00'))
