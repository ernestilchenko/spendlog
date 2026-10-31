from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user
from spendlog.savings.models import SavingsEntry, SavingsGoal


class GoalDeleteTests(TestCase):
    def test_deletes_goal_with_entries(self):
        user = create_user()
        self.client.force_login(user)
        goal = SavingsGoal.objects.create(user=user, name='Car')
        goal.entries.create(user=user, amount=Decimal('10'), amount_pln=Decimal('10'))
        response = self.client.post(reverse('savings:goal_delete', args=[goal.pk]))
        self.assertRedirects(response, reverse('savings:goal_list'))
        self.assertFalse(SavingsEntry.objects.exists())
