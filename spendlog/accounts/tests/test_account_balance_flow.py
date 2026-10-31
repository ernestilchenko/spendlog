from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from spendlog.accounts.models import Account
from spendlog.core.testing import create_user, get_category
from spendlog.savings.models import SavingsGoal

FETCH = 'spendlog.currencies.nbp.fetch_nbp_rates'


class AccountBalanceFlowTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        start = timezone.now() - timedelta(days=1)
        self.pln = Account.objects.create(user=self.user, name='Card', currency='PLN', opening_balance=Decimal('1000'), opening_date=start)
        self.eur = Account.objects.create(user=self.user, name='Card', currency='EUR', opening_balance=Decimal('30'), opening_date=start)
        self.now = timezone.localtime().strftime('%Y-%m-%dT%H:%M')

    def add_transaction(self, **overrides):
        data = {
            'kind': 'expense',
            'amount': '100',
            'currency': 'PLN',
            'account': '',
            'merchant': 'Shop',
            'category': get_category(self.user, 'Groceries').pk,
            'occurred_at': self.now,
            'note': '',
        }
        data.update(overrides)
        return self.client.post(reverse('transactions:transaction_create'), data)

    def balances(self):
        with patch(FETCH, return_value={timezone.localdate(): Decimal('4')}):
            response = self.client.get(reverse('dashboard:home'))
        return {item.account.currency: item.balance for item in response.context['account_balances']}, response

    def test_expense_and_income_move_pln_balance(self):
        self.add_transaction(amount='100')
        self.add_transaction(kind='income', amount='5100', category=get_category(self.user, 'Salary').pk)
        balances, _ = self.balances()
        self.assertEqual(balances['PLN'], Decimal('6000'))

    def test_euro_payment_goes_to_euro_account(self):
        with patch(FETCH, return_value={timezone.localdate(): Decimal('4')}):
            self.add_transaction(amount='12.50', currency='EUR')
        balances, _ = self.balances()
        self.assertEqual(balances, {'PLN': Decimal('1000'), 'EUR': Decimal('17.50')})

    def test_explicit_account_in_other_currency_is_converted(self):
        with patch(FETCH, return_value={timezone.localdate(): Decimal('4')}):
            self.add_transaction(amount='10', currency='EUR', account=self.pln.pk)
        balances, _ = self.balances()
        self.assertEqual(balances['PLN'], Decimal('960'))

    def test_savings_deposit_from_account_and_old_savings(self):
        goal = SavingsGoal.objects.create(user=self.user, name='Car', target_amount=Decimal('40000'))
        url = reverse('savings:entry_create', args=[goal.pk])
        entry = {'kind': 'deposit', 'amount': '300', 'currency': 'PLN', 'occurred_at': self.now, 'note': ''}
        self.client.post(url, {**entry, 'account': self.pln.pk})
        self.client.post(url, {**entry, 'amount': '5000', 'account': ''})
        balances, response = self.balances()
        self.assertEqual(balances['PLN'], Decimal('700'))
        self.assertEqual(response.context['in_savings'], Decimal('5300'))
        self.assertEqual(response.context['net_worth'], Decimal('700') + Decimal('120') + Decimal('5300'))

    def test_transactions_before_opening_date_are_ignored(self):
        before = (timezone.localtime() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M')
        self.add_transaction(amount='100', occurred_at=before)
        balances, _ = self.balances()
        self.assertEqual(balances['PLN'], Decimal('1000'))
