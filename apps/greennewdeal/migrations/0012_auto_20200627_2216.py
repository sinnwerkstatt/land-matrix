# Generated by Django 2.2.13 on 2020-06-27 20:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('greennewdeal', '0011_auto_20200626_1404'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deal',
            old_name='annual_leasing_fees_comment',
            new_name='annual_leasing_fee_comment',
        ),
    ]
