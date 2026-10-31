from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user


class ApplePaySetupTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.url = reverse('integrations:apple_pay_setup')

    def test_shows_endpoint_url(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['endpoint_url'], 'http://testserver/api/apple-pay/')
        self.assertIsNone(response.context['token'])
