from django.test import TestCase
from django.urls import reverse

from spendlog.core.testing import create_user


class GoalCreateTests(TestCase):
    def test_creates_goal(self):
        user = create_user()
        self.client.force_login(user)
        response = self.client.post(reverse('savings:goal_create'), {
            'name': 'Car',
            'target_amount': '40000',
            'target_date': '2027-12-01',
            'color': '#c96442',
        })
        goal = user.savings_goals.get()
        self.assertRedirects(response, reverse('savings:goal_detail', args=[goal.pk]))
        self.assertEqual(str(goal.target_amount), '40000.00')

    def test_target_is_optional(self):
        user = create_user()
        self.client.force_login(user)
        self.client.post(reverse('savings:goal_create'), {'name': 'Cushion', 'color': '#c96442'})
        self.assertIsNone(user.savings_goals.get().target_amount)
