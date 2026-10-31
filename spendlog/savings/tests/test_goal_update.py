from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user
from spendlog.savings.models import SavingsGoal


class GoalUpdateTests(TestCase):
    def test_archives_goal(self):
        user = create_user()
        self.client.force_login(user)
        goal = SavingsGoal.objects.create(user=user, name='Car')
        response = self.client.post(reverse('savings:goal_update', args=[goal.pk]), {
            'name': 'Car',
            'color': '#000000',
            'is_archived': 'on',
        })
        self.assertRedirects(response, reverse('savings:goal_detail', args=[goal.pk]))
        goal.refresh_from_db()
        self.assertTrue(goal.is_archived)
