# Generated by Django 4.1 on 2023-07-18 02:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock_prediction_dashboard', '0004_updateinfo'),
    ]

    operations = [
        migrations.CreateModel(
            name='stockPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Ticker', models.CharField(max_length=10)),
                ('date', models.DateField(default=datetime.date.today)),
                ('stock_price', models.FloatField(default=0)),
            ],
        ),
        migrations.DeleteModel(
            name='updateInfo',
        ),
    ]
