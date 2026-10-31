from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from spendlog.accounts.models import Account
from spendlog.core.testing import create_user

FETCH = 'spendlog.currencies.nbp.fetch_nbp_rates'


class AccountListTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        start = timezone.now() - timedelta(hours=1)
        Account.objects.create(user=self.user, name='Card', currency='PLN', opening_balance=Decimal('11190.40'), opening_date=start)
        Account.objects.create(user=self.user, name='Card', currency='EUR', opening_balance=Decimal('28.11'), opening_date=start)
        Account.objects.create(user=create_user('other@example.com'), name='Hidden', opening_balance=Decimal('1'))

    def test_balances_and_total_in_pln(self):
        with patch(FETCH, return_value={timezone.localdate(): Decimal('4.40')}):
            response = self.client.get(reverse('accounts:account_list'))
        balances = {(item.account.currency, item.balance) for item in response.context['balances']}
        self.assertEqual(balances, {('PLN', Decimal('11190.40')), ('EUR', Decimal('28.11'))})
        self.assertEqual(response.context['total_pln'], Decimal('11314.08'))
