# Generated by Django 4.1 on 2023-07-31 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock_prediction_dashboard', '0006_lastupdate'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockprice',
            name='predict_change',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='stockprice',
            name='stock_change',
            field=models.FloatField(default=0),
        ),
    ]
