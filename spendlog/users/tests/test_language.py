from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user


class LanguageSwitchTests(TestCase):
    def setUp(self):
        self.client.force_login(create_user())
        self.url = reverse('set_language')

    def test_switch_to_polish(self):
        response = self.client.post(self.url, {'language': 'pl', 'next': '/'})
        self.assertRedirects(response, '/')
        page = self.client.get(reverse('dashboard:home'))
        self.assertContains(page, 'Przegląd')
        self.assertContains(page, 'Wyloguj')

    def test_switch_to_ukrainian_translates_default_categories(self):
        self.client.post(self.url, {'language': 'uk', 'next': '/'})
        page = self.client.get(reverse('categories:category_list'))
        self.assertContains(page, 'Продукти')
        self.assertContains(page, 'Категорії')

    def test_login_page_has_language_switch(self):
        self.client.logout()
        page = self.client.get(reverse('users:login'), headers={'Accept-Language': 'pl'})
        self.assertContains(page, 'Gdzie się podziały pieniądze?')
        self.assertContains(page, 'name="language" value="uk"')
