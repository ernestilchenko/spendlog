from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user
from spendlog.savings.models import SavingsGoal


class EntryDeleteTests(TestCase):
    def test_deletes_own_entry(self):
        user = create_user()
        self.client.force_login(user)
        goal = SavingsGoal.objects.create(user=user, name='Car')
        entry = goal.entries.create(user=user, amount=Decimal('10'), amount_pln=Decimal('10'))
        response = self.client.post(reverse('savings:entry_delete', args=[entry.pk]))
        self.assertRedirects(response, reverse('savings:goal_detail', args=[goal.pk]))
        self.assertFalse(goal.entries.exists())

    def test_foreign_entry_is_404(self):
        other = create_user('other@example.com')
        goal = SavingsGoal.objects.create(user=other, name='Hidden')
        entry = goal.entries.create(user=other, amount=Decimal('10'), amount_pln=Decimal('10'))
        self.client.force_login(create_user())
        self.assertEqual(self.client.post(reverse('savings:entry_delete', args=[entry.pk])).status_code, 404)
