from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user


class AccountCreateTests(TestCase):
    def test_creates_account_with_opening_balance(self):
        user = create_user()
        self.client.force_login(user)
        response = self.client.post(reverse('accounts:account_create'), {
            'name': 'Card',
            'currency': 'PLN',
            'opening_balance': '11190.40',
            'opening_date': '2026-10-31T12:00',
            'color': '#6b6a65',
        })
        self.assertRedirects(response, reverse('accounts:account_list'))
        self.assertEqual(user.accounts.get().opening_balance, Decimal('11190.40'))
