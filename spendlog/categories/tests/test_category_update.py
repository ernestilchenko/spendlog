from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user, get_category


class CategoryUpdateTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)

    def test_sets_budget(self):
        groceries = get_category(self.user, 'Groceries')
        url = reverse('categories:category_update', args=[groceries.pk])
        response = self.client.post(url, {'name': 'Groceries', 'kind': 'expense', 'color': '#16a34a', 'monthly_budget': '1200'})
        self.assertRedirects(response, reverse('categories:category_list'))
        groceries.refresh_from_db()
        self.assertEqual(str(groceries.monthly_budget), '1200.00')

    def test_foreign_category_is_404(self):
        foreign = get_category(create_user('other@example.com'), 'Groceries')
        response = self.client.get(reverse('categories:category_update', args=[foreign.pk]))
        self.assertEqual(response.status_code, 404)
