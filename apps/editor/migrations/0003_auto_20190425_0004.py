# Generated by Django 2.1.8 on 2019-04-24 22:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0002_userregionalinfo_information'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userregionalinfo',
            name='super_user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='super_user', to=settings.AUTH_USER_MODEL),
        ),
    ]