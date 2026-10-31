from django.test import TestCase
from django.urls import reverse

from spendlog.accounts.models import Account
from spendlog.core.testing import create_transaction, create_user


class AccountDeleteTests(TestCase):
    def test_delete_keeps_transactions(self):
        user = create_user()
        self.client.force_login(user)
        account = Account.objects.create(user=user, name='Card')
        transaction = create_transaction(user)
        transaction.account = account
        transaction.save()
        response = self.client.post(reverse('accounts:account_delete', args=[account.pk]))
        self.assertRedirects(response, reverse('accounts:account_list'))
        transaction.refresh_from_db()
        self.assertIsNone(transaction.account)
