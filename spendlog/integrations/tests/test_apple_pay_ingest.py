import json
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from spendlog.categories.models import MerchantRule
from spendlog.core.choices import TransactionSource
from spendlog.core.testing import create_user, get_category
from spendlog.integrations.models import ApiToken
from spendlog.integrations.services import issue_token

SUGGEST = 'spendlog.categories.services.suggest_category_name'


class ApplePayIngestTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.token = issue_token(self.user)
        self.url = reverse('integrations:apple_pay_ingest')

    def send(self, payload, token=None):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Token {token or self.token}'},
        )

    def test_rejects_missing_token(self):
        response = self.client.post(self.url, data='{}', content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_rejects_wrong_token(self):
        response = self.send({'amount': '5'}, token='wrong')
        self.assertEqual(response.status_code, 401)
        self.assertFalse(self.user.transactions.exists())

    def test_rule_category_and_polish_amount(self):
        MerchantRule.objects.create(user=self.user, pattern='żabka', category=get_category(self.user, 'Groceries'))
        response = self.send({'amount': '1 018,50 zł', 'merchant': 'Żabka Z1234', 'card': 'Visa 1234'})
        self.assertEqual(response.status_code, 201)
        transaction = self.user.transactions.get()
        self.assertEqual(transaction.amount, Decimal('1018.50'))
        self.assertEqual(transaction.category.name, 'Groceries')
        self.assertEqual(transaction.source, TransactionSource.APPLE_PAY)
        self.assertEqual(transaction.card, 'Visa 1234')
        self.assertEqual(response.json()['message'], 'Żabka Z1234 · 1 018,50 zł → Groceries')

    @patch(SUGGEST, return_value='Cafes & restaurants')
    def test_ai_category_is_saved_as_rule(self, suggest):
        response = self.send({'amount': 'PLN 24.90', 'merchant': 'Costa Coffee'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.user.transactions.get().category.name, 'Cafes & restaurants')
        self.assertEqual(self.user.merchant_rules.get().pattern, 'costa coffee')
        self.send({'amount': '12', 'merchant': 'Costa Coffee'})
        suggest.assert_called_once()

    @patch(SUGGEST, return_value=None)
    def test_falls_back_to_other(self, suggest):
        self.send({'amount': 7, 'merchant': 'P.H.U. KOWALSKI'})
        self.assertEqual(self.user.transactions.get().category.name, 'Other')

    def test_works_without_api_key(self):
        response = self.send({'amount': 3.5, 'merchant': 'Kiosk'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.user.transactions.get().category.name, 'Other')

    def test_rejects_bad_amount(self):
        for amount in ('', 'abc', '0', True):
            response = self.send({'amount': amount, 'merchant': 'X'})
            self.assertEqual(response.status_code, 400)
        self.assertFalse(self.user.transactions.exists())

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_form_encoded_body(self):
        with patch(SUGGEST, return_value=None):
            response = self.client.post(
                self.url,
                {'amount': '9,99', 'merchant': 'Lidl'},
                headers={'Authorization': f'Token {self.token}'},
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.user.transactions.get().amount, Decimal('9.99'))

    def test_marks_token_as_used(self):
        with patch(SUGGEST, return_value=None):
            self.send({'amount': '1', 'merchant': 'Kiosk'})
        self.assertIsNotNone(ApiToken.objects.get(user=self.user).last_used_at)
