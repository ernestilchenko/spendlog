import logging

import anthropic
from django.conf import settings
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    'You sort card payments made in Poland into personal budget categories. '
    'You get the merchant name exactly as the bank reports it and the list of the user\'s categories. '
    'Answer with the exact name of the single best matching category from the list. '
    'If the merchant name gives no reasonable hint, answer with an empty string.'
)


class CategoryChoice(BaseModel):
    category: str


def suggest_category_name(merchant, category_names):
    if not settings.ANTHROPIC_API_KEY or not merchant or not category_names:
        return None
    client = anthropic.Anthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        timeout=settings.CATEGORIZER_TIMEOUT_SECONDS,
        max_retries=1,
    )
    prompt = f'Merchant: {merchant}\n\nCategories:\n' + '\n'.join(f'- {name}' for name in category_names)
    try:
        response = client.beta.messages.parse(
            model=settings.CATEGORIZER_MODEL,
            max_tokens=2048,
            betas=['server-side-fallback-2026-07-01'],
            fallbacks='default',
            output_config={'effort': 'low'},
            output_format=CategoryChoice,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': prompt}],
        )
    except anthropic.RateLimitError:
        logger.warning('Categorizer rate limited for merchant %s', merchant)
        return None
    except anthropic.APIStatusError as error:
        logger.warning('Categorizer API error %s: %s', error.status_code, error.message)
        return None
    except anthropic.APIConnectionError:
        logger.warning('Categorizer could not reach the API')
        return None
    if response.stop_reason == 'refusal' or response.parsed_output is None:
        return None
    name = response.parsed_output.category.strip()
    return name if name in category_names else None
