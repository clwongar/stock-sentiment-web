# Generated by Django 4.1 on 2023-06-19 08:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock_prediction_dashboard', '0002_stockinfo_imageurl_stockinfo_latestprice_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stocksentiment',
            old_name='symbol',
            new_name='Ticker',
        ),
    ]