from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from spendlog.core.choices import SavingsEntryKind
from spendlog.core.testing import create_user
from spendlog.savings.models import SavingsGoal


class GoalDetailTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)

    @patch('spendlog.savings.services.timezone.localdate', return_value=date(2026, 11, 15))
    def test_progress_and_monthly_need(self, localdate):
        goal = SavingsGoal.objects.create(user=self.user, name='Car', target_amount=Decimal('12000'), target_date=date(2027, 11, 1))
        goal.entries.create(user=self.user, amount=Decimal('3000'), amount_pln=Decimal('3000'))
        goal.entries.create(user=self.user, kind=SavingsEntryKind.WITHDRAWAL, amount=Decimal('600'), amount_pln=Decimal('600'))
        progress = self.client.get(reverse('savings:goal_detail', args=[goal.pk])).context['progress']
        self.assertEqual(progress.saved, Decimal('2400'))
        self.assertEqual(progress.percent, 20)
        self.assertEqual(progress.remaining, Decimal('9600'))
        self.assertEqual(progress.months_left, 12)
        self.assertEqual(progress.monthly_needed, Decimal('800.00'))

    def test_foreign_goal_is_404(self):
        goal = SavingsGoal.objects.create(user=create_user('other@example.com'), name='Hidden')
        self.assertEqual(self.client.get(reverse('savings:goal_detail', args=[goal.pk])).status_code, 404)
