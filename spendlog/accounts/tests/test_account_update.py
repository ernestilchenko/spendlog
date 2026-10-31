from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from spendlog.accounts.models import Account
from spendlog.core.testing import create_user


class AccountUpdateTests(TestCase):
    def test_corrects_balance(self):
        user = create_user()
        self.client.force_login(user)
        account = Account.objects.create(user=user, name='Card', opening_balance=Decimal('10'))
        response = self.client.post(reverse('accounts:account_update', args=[account.pk]), {
            'name': 'mBank',
            'currency': 'PLN',
            'opening_balance': '20',
            'opening_date': '2026-10-31T12:00',
            'color': '#000000',
        })
        self.assertRedirects(response, reverse('accounts:account_list'))
        account.refresh_from_db()
        self.assertEqual((account.name, account.opening_balance), ('mBank', Decimal('20')))

    def test_foreign_account_is_404(self):
        account = Account.objects.create(user=create_user('other@example.com'), name='Hidden')
        self.client.force_login(create_user())
        self.assertEqual(self.client.get(reverse('accounts:account_update', args=[account.pk])).status_code, 404)
