from django.conf import settings
from django.db import models

from spendlog.core.choices import TokenPurpose
from spendlog.core.models import TimeStampedModel


class ApiToken(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_tokens')
    purpose = models.CharField(max_length=20, choices=TokenPurpose, default=TokenPurpose.APPLE_PAY)
    key_hash = models.CharField(max_length=64, unique=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'purpose'), name='unique_api_token_per_purpose'),
        ]

    def __str__(self):
        return f'{self.get_purpose_display()} token of {self.user}'
