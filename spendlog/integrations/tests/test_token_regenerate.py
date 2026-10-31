import json

from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user
from spendlog.integrations.models import ApiToken


class TokenRegenerateTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.url = reverse('integrations:token_regenerate')
        self.setup_url = reverse('integrations:apple_pay_setup')

    def test_token_is_shown_once_and_works(self):
        response = self.client.post(self.url, follow=True)
        raw_token = response.context['new_token']
        self.assertTrue(raw_token)
        self.assertIsNone(self.client.get(self.setup_url).context['new_token'])
        self.assertNotEqual(ApiToken.objects.get(user=self.user).key_hash, raw_token)
        ingest = self.client.post(
            reverse('integrations:apple_pay_ingest'),
            data=json.dumps({'amount': '1', 'merchant': ''}),
            content_type='application/json',
            headers={'Authorization': f'Token {raw_token}'},
        )
        self.assertEqual(ingest.status_code, 201)

    def test_new_token_invalidates_old_one(self):
        old_token = self.client.post(self.url, follow=True).context['new_token']
        self.client.post(self.url)
        response = self.client.post(
            reverse('integrations:apple_pay_ingest'),
            data=json.dumps({'amount': '1'}),
            content_type='application/json',
            headers={'Authorization': f'Token {old_token}'},
        )
        self.assertEqual(response.status_code, 401)

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
