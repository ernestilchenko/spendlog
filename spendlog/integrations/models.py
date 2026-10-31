from django.conf import settings
from django.db import models

from spendlog.core.models import TimeStampedModel


class ApiToken(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_token')
    key_hash = models.CharField(max_length=64, unique=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'API token of {self.user}'
