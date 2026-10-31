from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user


class CategoryCreateTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.url = reverse('categories:category_create')

    def test_creates_category_with_budget(self):
        response = self.client.post(self.url, {'name': 'Gym', 'kind': 'expense', 'color': '#ff0000', 'monthly_budget': '150'})
        self.assertRedirects(response, reverse('categories:category_list'))
        category = self.user.categories.get(name='Gym')
        self.assertEqual(str(category.monthly_budget), '150.00')

    def test_rejects_duplicate_name_of_same_kind(self):
        response = self.client.post(self.url, {'name': 'Groceries', 'kind': 'expense', 'color': '#ff0000'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
