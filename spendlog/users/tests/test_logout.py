from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user


class LogoutTests(TestCase):
    def test_logout_ends_session(self):
        self.client.force_login(create_user())
        response = self.client.post(reverse('users:logout'))
        self.assertRedirects(response, reverse('users:login'))
        self.assertEqual(self.client.get(reverse('dashboard:home')).status_code, 302)
