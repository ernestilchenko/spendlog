from django.core.management.base import BaseCommand

from spendlog.banking.services import bank_configured, sync_all


class Command(BaseCommand):
    help = 'Import new transactions from every connected bank'

    def handle(self, *args, **options):
        if not bank_configured():
            self.stdout.write('Bank sync is not configured')
            return
        self.stdout.write(f'Imported {sync_all()} transactions')
