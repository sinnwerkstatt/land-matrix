# Generated by Django 2.2.14 on 2020-08-13 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landmatrix', '0021_auto_20200724_1520'),
    ]

    operations = [
        migrations.AddField(
            model_name='deal',
            name='cached_has_no_known_investor',
            field=models.BooleanField(default=True),
        ),
    ]
