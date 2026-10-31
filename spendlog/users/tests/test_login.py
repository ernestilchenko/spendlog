from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import PASSWORD, create_user


class LoginTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.url = reverse('users:login')

    def test_login_with_email_redirects_to_dashboard(self):
        response = self.client.post(self.url, {'username': self.user.email, 'password': PASSWORD})
        self.assertRedirects(response, reverse('dashboard:home'))

    def test_wrong_password_shows_form_again(self):
        response = self.client.post(self.url, {'username': self.user.email, 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertRedirects(response, f'{self.url}?next=/')

    def test_new_user_gets_default_categories(self):
        self.assertTrue(self.user.categories.filter(name='Groceries').exists())
        self.assertTrue(self.user.categories.filter(name='Salary').exists())
