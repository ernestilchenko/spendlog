from decimal import Decimal

from django.db import migrations, models
from django.db.models import F


def copy_amount_to_pln(apps, schema_editor):
    apps.get_model('transactions', 'Transaction').objects.update(amount_pln=F('amount'))


class Migration(migrations.Migration):
    dependencies = [
        ('transactions', '0003_verbose_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='currency',
            field=models.CharField(
                choices=[('PLN', 'PLN'), ('EUR', 'EUR'), ('USD', 'USD'), ('UAH', 'UAH'), ('GBP', 'GBP'), ('CHF', 'CHF'), ('CZK', 'CZK')],
                default='PLN',
                max_length=3,
                verbose_name='currency',
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='exchange_rate',
            field=models.DecimalField(decimal_places=6, default=Decimal('1'), max_digits=12, verbose_name='exchange rate'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='amount_pln',
            field=models.DecimalField(decimal_places=2, max_digits=12, null=True, verbose_name='amount in PLN'),
        ),
        migrations.RunPython(copy_amount_to_pln, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='transaction',
            name='amount_pln',
            field=models.DecimalField(decimal_places=2, max_digits=12, verbose_name='amount in PLN'),
        ),
    ]
