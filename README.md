# Spendlog

Personal budget tracker. Apple Pay payments arrive automatically from an iPhone Shortcuts automation and get a category on their own: first from your merchant rules, then from Claude, then `Other`.

Django 6 + Django templates, PostgreSQL. Project layout follows *Two Scoops of Django*: split settings and requirements, a custom user model, small apps with function-based views and a service layer.

## Apps

| App | What it does |
| --- | --- |
| `core` | `TimeStampedModel`, shared choices, month helpers, money formatting |
| `users` | Email-based custom user, login/logout. New users get default categories |
| `categories` | Categories with optional monthly budgets, merchant rules, auto-categorization (`services.categorize_expense`, `ai.suggest_category_name`) |
| `transactions` | Expenses and income: list with month/type/category filters, create, edit, delete |
| `integrations` | `POST /api/apple-pay/` for the Shortcut, API token management |
| `dashboard` | Month overview: totals, budget left, spending by category, latest transactions |

## Local setup

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements/local.txt
cp .env.example .env
createdb spendlog
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

Tests (endpoints only, run on Postgres):

```bash
DJANGO_SETTINGS_MODULE=config.settings.test .venv/bin/python manage.py test
```

## Environment

| Variable | Notes |
| --- | --- |
| `SECRET_KEY` | required |
| `DATABASE_URL` | required, e.g. `postgres://user@localhost:5432/spendlog` |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | comma-separated, production |
| `ANTHROPIC_API_KEY` | optional. Without it, unknown merchants go to `Other` |
| `CATEGORIZER_MODEL` | defaults to `claude-opus-5` |

## Categorization

1. Merchant rules: the longest rule whose text is contained in the merchant name wins.
2. Claude picks one of your expense categories. The answer is saved as a rule, so the same merchant never costs a second API call.
3. Fallback category `Other`.

Ticking “Always use this category for this merchant” on a transaction also creates or updates a rule.

## Apple Pay Shortcut

Create a token on the **Apple Pay** page, then on the iPhone: Shortcuts → Automation → + → **Transaction** → Run Immediately → **Get Contents of URL**:

- URL: `https://<your domain>/api/apple-pay/`, method `POST`
- Header `Authorization: Token <token>`
- JSON body: `amount` = Amount, `merchant` = Merchant, `card` = Card or Pass

The response has a `message` field (`Żabka · 18,50 zł → Groceries`) that can be shown with **Show Notification**. Only tap-to-pay with the iPhone triggers the automation; add physical card, BLIK and transfers manually.

## Deploy

The `Dockerfile` runs migrations and gunicorn on port 8000 with `config.settings.production`. It is meant for a Coolify app on tinynest with a Postgres resource and a Cloudflare Tunnel hostname. HTTPS is required for the Shortcut.
