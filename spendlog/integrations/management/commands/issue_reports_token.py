from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from spendlog.core.choices import TokenPurpose
from spendlog.integrations.services import issue_token


class Command(BaseCommand):
    help = 'Create or replace the read-only reports API token of a user and print it once'

    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, *args, email, **options):
        user = get_user_model().objects.filter(email__iexact=email).first()
        if user is None:
            raise CommandError(f'No user with email {email}')
        self.stdout.write(issue_token(user, TokenPurpose.REPORTS))
