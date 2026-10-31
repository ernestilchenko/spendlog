from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user
from spendlog.savings.models import SavingsGoal


class GoalListTests(TestCase):
    def test_lists_own_goals_with_total(self):
        user = create_user()
        goal = SavingsGoal.objects.create(user=user, name='Car', target_amount=Decimal('1000'))
        goal.entries.create(user=user, amount=Decimal('300'), amount_pln=Decimal('300'))
        SavingsGoal.objects.create(user=create_user('other@example.com'), name='Hidden')
        self.client.force_login(user)
        response = self.client.get(reverse('savings:goal_list'))
        self.assertEqual([item.goal.name for item in response.context['progress_list']], ['Car'])
        self.assertEqual(response.context['total_saved'], Decimal('300'))
