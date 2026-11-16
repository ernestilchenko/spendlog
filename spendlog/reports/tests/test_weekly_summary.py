from datetime import date, datetime, time
from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from spendlog.core.choices import SavingsEntryKind, TokenPurpose, TransactionKind
from spendlog.core.testing import create_transaction, create_user, get_category
from spendlog.integrations.services import issue_token
from spendlog.savings.models import SavingsEntry, SavingsGoal

TODAY = date(2026, 11, 18)


def at(day, hour=12):
    return timezone.make_aware(datetime.combine(day, time(hour)))


class WeeklySummaryTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.token = issue_token(self.user, TokenPurpose.REPORTS)
        self.url = reverse('reports:weekly_summary')
        patcher = patch('django.utils.timezone.localdate', return_value=TODAY)
        patcher.start()
        self.addCleanup(patcher.stop)

    def get(self, token=None):
        return self.client.get(self.url, headers={'Authorization': f'Token {token or self.token}'})

    def test_rejects_missing_token(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_rejects_apple_pay_token(self):
        apple_pay = issue_token(self.user)
        self.assertEqual(self.get(apple_pay).status_code, 401)

    def test_reports_token_does_not_replace_apple_pay_token(self):
        apple_pay = issue_token(self.user)
        issue_token(self.user, TokenPurpose.REPORTS)
        self.assertEqual(self.user.api_tokens.count(), 2)
        response = self.client.post(
            reverse('integrations:apple_pay_ingest'),
            data='{"amount": "5", "merchant": "Shop"}',
            content_type='application/json',
            headers={'Authorization': f'Token {apple_pay}'},
        )
        self.assertEqual(response.status_code, 201)

    def test_rejects_post(self):
        response = self.client.post(self.url, headers={'Authorization': f'Token {self.token}'})
        self.assertEqual(response.status_code, 405)

    def test_week_totals_and_previous_week(self):
        groceries = get_category(self.user, 'Groceries')
        create_transaction(self.user, '40.00', category=groceries, occurred_at=at(date(2026, 11, 16), 0))
        create_transaction(self.user, '15.50', category=None, occurred_at=at(TODAY))
        create_transaction(self.user, '300.00', kind=TransactionKind.INCOME, occurred_at=at(TODAY))
        create_transaction(self.user, '70.00', category=groceries, occurred_at=at(date(2026, 11, 15), 23))
        create_transaction(self.user, '1.00', occurred_at=at(date(2026, 11, 23)))
        response = self.get()
        self.assertEqual(response.status_code, 200)
        week = response.json()['week']
        self.assertEqual((week['start'], week['end']), ('2026-11-16', '2026-11-22'))
        self.assertEqual(week['expense'], '55.50')
        self.assertEqual(week['income'], '300.00')
        self.assertEqual(week['previous_expense'], '70.00')
        self.assertEqual(week['transactions'], 3)
        self.assertEqual(
            week['top_categories'],
            [{'name': 'Groceries', 'spent': '40.00'}, {'name': 'Uncategorized', 'spent': '15.50'}],
        )

    def test_month_budget_left(self):
        groceries = get_category(self.user, 'Groceries')
        groceries.monthly_budget = Decimal('500.00')
        groceries.save()
        create_transaction(self.user, '120.00', category=groceries, occurred_at=at(date(2026, 11, 3)))
        create_transaction(self.user, '30.00', category=None, occurred_at=at(date(2026, 11, 4)))
        create_transaction(self.user, '999.00', category=groceries, occurred_at=at(date(2026, 10, 31)))
        month = self.get().json()['month']
        self.assertEqual(month, {'expense': '150.00', 'budget_total': '500.00', 'budget_left': '380.00'})

    def test_goal_progress_and_weekly_savings(self):
        goal = SavingsGoal.objects.create(
            user=self.user,
            name='Apartment',
            target_amount=Decimal('85000.00'),
            target_date=date(2027, 11, 1),
        )
        SavingsGoal.objects.create(user=self.user, name='Old', is_archived=True)
        for amount, day, kind in (
            ('20000.00', date(2026, 10, 1), SavingsEntryKind.DEPOSIT),
            ('1500.00', date(2026, 11, 17), SavingsEntryKind.DEPOSIT),
            ('500.00', date(2026, 11, 18), SavingsEntryKind.WITHDRAWAL),
        ):
            SavingsEntry.objects.create(
                user=self.user,
                goal=goal,
                kind=kind,
                amount=Decimal(amount),
                amount_pln=Decimal(amount),
                occurred_at=at(day),
            )
        data = self.get().json()
        self.assertEqual(data['week']['saved'], '1000.00')
        self.assertEqual(data['goals'], [{
            'name': 'Apartment',
            'saved': '21000.00',
            'target': '85000.00',
            'remaining': '64000.00',
            'percent': 24,
            'target_date': '2027-11-01',
            'monthly_needed': '5333.34',
            'saved_this_week': '1000.00',
        }])

    def test_empty_week(self):
        data = self.get().json()
        self.assertEqual(data['week']['expense'], '0.00')
        self.assertEqual(data['week']['top_categories'], [])
        self.assertEqual(data['month']['budget_left'], None)
        self.assertEqual(data['goals'], [])

    def test_other_users_data_is_excluded(self):
        other = create_user('other@example.com')
        create_transaction(other, '77.00', occurred_at=at(TODAY))
        self.assertEqual(self.get().json()['week']['expense'], '0.00')


class IssueReportsTokenCommandTests(TestCase):
    def test_prints_working_token(self):
        user = create_user()
        with patch('sys.stdout') as stdout:
            call_command('issue_reports_token', user.email, stdout=stdout)
        token = stdout.write.call_args[0][0].strip()
        response = self.client.get(reverse('reports:weekly_summary'), headers={'Authorization': f'Token {token}'})
        self.assertEqual(response.status_code, 200)
