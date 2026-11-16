from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from spendlog.accounts.models import Account
from spendlog.banking.client import EnableBankingError
from spendlog.banking.models import BankConnection, PassThroughRule
from spendlog.categories.models import Category, MerchantRule
from spendlog.core.choices import BankConnectionStatus, TransactionKind, TransactionSource
from spendlog.core.testing import create_user, get_category
from spendlog.transactions.models import Transaction

BANK = override_settings(ENABLE_BANKING_APP_ID='app-id', ENABLE_BANKING_KEY_PATH='/run/secrets/key.pem')
TODAY = date(2026, 11, 20)


def row(ref, amount, indicator='DBIT', text='', creditor=None, debtor=None, day='2026-11-18', status='BOOK', code=None):
    return {
        'entry_reference': ref,
        'transaction_amount': {'amount': amount, 'currency': 'PLN'},
        'credit_debit_indicator': indicator,
        'status': status,
        'booking_date': day,
        'transaction_date': day,
        'remittance_information': [text] if text else [],
        'creditor': {'name': creditor} if creditor else None,
        'debtor': {'name': debtor} if debtor else None,
        'bank_transaction_code': code,
    }


CARD = '557464------0394 Ernest Ilchenko Pruszkow LIDL PRUSA POL 9,99 PLN 2026-11-18'


class FakeClient:
    def __init__(self):
        self.transactions_by_uid = {'acc-pln': []}
        self.balance = '1000.00'
        self.started = []
        self.error = None

    def start_auth(self, aspsp_name, country, redirect_url, state, valid_until):
        self.started.append({'aspsp': aspsp_name, 'country': country, 'redirect_url': redirect_url, 'state': state})
        return 'https://bank.example/authorize'

    def create_session(self, code):
        return {
            'session_id': 'session-1',
            'access': {'valid_until': '2027-05-19T10:00:00Z'},
            'accounts': [{'uid': 'acc-pln', 'currency': 'PLN', 'account_id': {'iban': 'PL35160014621738973660000001'}}],
        }

    def transactions(self, account_uid, date_from):
        if self.error:
            raise self.error
        return list(self.transactions_by_uid[account_uid])

    def balances(self, account_uid):
        return [{'balance_type': 'CLBD', 'balance_amount': {'amount': self.balance, 'currency': 'PLN'}}]


@BANK
class BankSyncTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.account = Account.objects.create(
            user=self.user,
            name='Card',
            opening_balance=Decimal('1000.00'),
            opening_date=timezone.make_aware(datetime(2026, 11, 1)),
        )
        Category.objects.create(user=self.user, name='Cash', kind=TransactionKind.EXPENSE)
        MerchantRule.objects.create(user=self.user, pattern='lidl', category=get_category(self.user, 'Groceries'))
        MerchantRule.objects.create(user=self.user, pattern='mapmaker', category=get_category(self.user, 'Salary'))
        self.fake = FakeClient()
        for target, value in (
            ('spendlog.banking.services.get_client', lambda: self.fake),
            ('django.utils.timezone.localdate', lambda *args: TODAY),
        ):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def connect(self, rows=()):
        self.fake.transactions_by_uid['acc-pln'] = list(rows)
        self.client.post(reverse('banking:connect'))
        state = self.fake.started[-1]['state']
        return self.client.get(reverse('banking:callback'), {'state': state, 'code': 'auth-code'})

    def sync(self, rows):
        self.fake.transactions_by_uid['acc-pln'] = list(rows)
        return self.client.post(reverse('banking:sync'))

    def test_overview_without_configuration(self):
        with override_settings(ENABLE_BANKING_APP_ID=''):
            response = self.client.get(reverse('banking:overview'))
            self.assertContains(response, 'not configured')
            response = self.client.post(reverse('banking:connect'))
        self.assertRedirects(response, reverse('banking:overview'))
        self.assertFalse(BankConnection.objects.exists())

    def test_connect_redirects_to_bank(self):
        response = self.client.post(reverse('banking:connect'))
        self.assertRedirects(response, 'https://bank.example/authorize', fetch_redirect_response=False)
        started = self.fake.started[0]
        self.assertEqual((started['aspsp'], started['country']), ('BNP Paribas', 'PL'))
        self.assertEqual(started['redirect_url'], 'http://testserver/bank/callback/')
        connection = BankConnection.objects.get()
        self.assertEqual((connection.status, connection.state), (BankConnectionStatus.PENDING, started['state']))

    def test_overview_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('banking:overview'))
        self.assertEqual(response.status_code, 302)

    def test_callback_links_account_and_imports(self):
        response = self.connect([
            row('card-1', '9.99', text=CARD),
            row('pending', '5.00', text=CARD, status='PDNG'),
        ])
        self.assertRedirects(response, reverse('banking:overview'))
        connection = BankConnection.objects.get()
        self.assertEqual(connection.status, BankConnectionStatus.ACTIVE)
        self.assertEqual(connection.valid_until.date(), date(2027, 5, 19))
        link = connection.links.get()
        self.assertEqual((link.account, link.iban), (self.account, 'PL35160014621738973660000001'))
        self.assertEqual(link.bank_balance, Decimal('1000.00'))
        transaction = self.user.transactions.get()
        self.assertEqual(transaction.merchant, 'Pruszkow LIDL PRUSA')
        self.assertEqual(transaction.category.name, 'Groceries')
        self.assertEqual(transaction.source, TransactionSource.BANK)
        self.assertEqual(transaction.external_id, 'eb:card-1')
        self.assertEqual(transaction.account, self.account)

    def test_callback_with_unknown_state(self):
        response = self.client.get(reverse('banking:callback'), {'state': 'forged', 'code': 'x'})
        self.assertRedirects(response, reverse('banking:overview'))
        self.assertFalse(BankConnection.objects.filter(status=BankConnectionStatus.ACTIVE).exists())

    def test_callback_of_another_user_is_rejected(self):
        self.client.post(reverse('banking:connect'))
        state = self.fake.started[-1]['state']
        self.client.force_login(create_user('other@example.com'))
        self.client.get(reverse('banking:callback'), {'state': state, 'code': 'x'})
        self.assertEqual(BankConnection.objects.get().status, BankConnectionStatus.PENDING)

    def test_bank_refusal_is_reported(self):
        self.client.post(reverse('banking:connect'))
        response = self.client.get(reverse('banking:callback'), {'error': 'access_denied'}, follow=True)
        self.assertContains(response, 'access_denied')
        self.assertEqual(BankConnection.objects.get().status, BankConnectionStatus.PENDING)

    def test_repeated_sync_does_not_duplicate(self):
        rows = [row('card-1', '9.99', text=CARD), row('card-2', '20.00', text=CARD)]
        self.connect(rows)
        self.sync(rows)
        self.assertEqual(self.user.transactions.count(), 2)

    def test_existing_manual_transaction_is_linked_instead_of_duplicated(self):
        manual = Transaction.objects.create(
            user=self.user,
            account=self.account,
            account_amount=Decimal('9.99'),
            amount=Decimal('9.99'),
            amount_pln=Decimal('9.99'),
            merchant='Lidl',
            occurred_at=timezone.make_aware(datetime.combine(date(2026, 11, 17), time(18))),
            source=TransactionSource.APPLE_PAY,
        )
        self.connect([row('card-1', '9.99', text=CARD)])
        manual.refresh_from_db()
        self.assertEqual(manual.external_id, 'eb:card-1')
        self.assertEqual(self.user.transactions.count(), 1)

    def test_cash_and_income(self):
        self.connect([
            row('atm', '800.00', text='557464------0394 Ernest Ilchenko LODZ Nowa Sukcesja POL 800,00 PLN 2026-11-18', code={'description': 'Wypłata gotówki'}),
            row('salary', '5000.00', 'CRDT', text='WYNAGRODZENIE', debtor='MAPMAKER.ONLINE SP. Z O.O.'),
            row('friend', '50.00', 'CRDT', text='zwrot', debtor='DANYLO'),
        ])
        by_ref = {t.external_id: t for t in self.user.transactions.select_related('category')}
        self.assertEqual(by_ref['eb:atm'].category.name, 'Cash')
        self.assertEqual(by_ref['eb:salary'].category.name, 'Salary')
        self.assertEqual(by_ref['eb:salary'].kind, TransactionKind.INCOME)
        self.assertEqual(by_ref['eb:friend'].category.name, 'Other income')

    def test_pass_through_income_keeps_own_part_and_skips_forward(self):
        PassThroughRule.objects.create(user=self.user, pattern='mapmaker', passed_on_amount=Decimal('3000.00'))
        self.connect([row('salary', '4995.00', 'CRDT', text='WYNAGRODZENIE ZA 10.2026', debtor='MAPMAKER.ONLINE', day='2026-11-10')])
        salary = self.user.transactions.get()
        self.assertEqual(salary.amount, Decimal('1995.00'))
        self.assertIn('3000.00 passed on', salary.note)
        self.sync([
            row('forward', '3000.00', text='Zwrot', creditor='Daria', day='2026-11-12'),
            row('rent', '3000.00', text='Czynsz', creditor='Landlord', day='2026-11-13'),
        ])
        self.assertEqual(
            sorted(self.user.transactions.values_list('external_id', flat=True)),
            ['eb:rent', 'eb:salary'],
        )
        self.assertTrue(self.user.ignored_bank_transactions.filter(external_id='eb:forward').exists())

    def test_deleted_bank_transaction_is_not_imported_again(self):
        rows = [row('card-1', '9.99', text=CARD)]
        self.connect(rows)
        transaction = self.user.transactions.get()
        self.client.post(reverse('transactions:transaction_delete', args=[transaction.pk]))
        self.sync(rows)
        self.assertFalse(self.user.transactions.exists())

    def test_transaction_without_ids_uses_stable_fingerprint(self):
        anonymous = row(None, '800.00', text='ATM', code={'description': 'Wypłata'})
        twin = dict(anonymous, balance_after_transaction={'amount': '200.00', 'currency': 'PLN'})
        self.connect([anonymous, twin])
        self.sync([anonymous, twin])
        self.assertEqual(self.user.transactions.count(), 2)

    def test_sync_error_is_shown_and_stored(self):
        self.connect()
        self.fake.error = EnableBankingError(503, 'bank is down')
        response = self.client.post(reverse('banking:sync'), follow=True)
        self.assertContains(response, 'bank is down')
        self.assertIn('bank is down', BankConnection.objects.get().last_error)

    def test_expired_access_is_not_synced(self):
        self.connect()
        BankConnection.objects.update(valid_until=timezone.now() - timedelta(days=1))
        self.sync([row('card-1', '9.99', text=CARD)])
        self.assertEqual(BankConnection.objects.get().status, BankConnectionStatus.EXPIRED)
        self.assertFalse(self.user.transactions.exists())

    def test_overview_shows_bank_and_spendlog_balance(self):
        self.connect([row('card-1', '9.99', text=CARD)])
        self.fake.balance = '990.01'
        self.sync([])
        response = self.client.get(reverse('banking:overview'))
        self.assertContains(response, 'PL35160014621738973660000001')
        self.assertEqual(response.context['links'][0]['difference'], Decimal('0'))

    def test_sync_without_connection(self):
        response = self.client.post(reverse('banking:sync'), follow=True)
        self.assertContains(response, 'Connect the bank first')

    def test_management_command_syncs_active_connections(self):
        self.connect()
        self.fake.transactions_by_uid['acc-pln'] = [row('card-1', '9.99', text=CARD)]
        out = StringIO()
        call_command('sync_bank', stdout=out)
        self.assertIn('Imported 1 transactions', out.getvalue())
