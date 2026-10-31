from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user


class CategoryListTests(TestCase):
    def test_lists_own_categories(self):
        user = create_user()
        create_user('other@example.com').categories.create(name='Foreign')
        self.client.force_login(user)
        response = self.client.get(reverse('categories:category_list'))
        names = {category.name for category in response.context['categories']}
        self.assertIn('Groceries', names)
        self.assertNotIn('Foreign', names)
        kinds = [category.kind for category in response.context['categories']]
        self.assertEqual(kinds, sorted(kinds))
