import json
import logging
import urllib.error
import urllib.request
from datetime import date
from decimal import Decimal

from django.conf import settings

logger = logging.getLogger(__name__)


def fetch_nbp_rates(currency, start, end):
    url = f'{settings.NBP_API_URL}/rates/a/{currency.lower()}/{start.isoformat()}/{end.isoformat()}/?format=json'
    try:
        with urllib.request.urlopen(url, timeout=settings.NBP_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            logger.warning('NBP returned %s for %s', error.code, url)
        return {}
    except (urllib.error.URLError, TimeoutError, ValueError):
        logger.warning('NBP is unreachable for %s', url)
        return {}
    return {date.fromisoformat(row['effectiveDate']): Decimal(str(row['mid'])) for row in payload.get('rates', [])}
