# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_auto_20160509_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationemail',
            name='created_on',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created On'),
        ),
    ]
