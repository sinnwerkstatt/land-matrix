# Generated by Django 2.2.14 on 2020-09-28 13:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcms', '0003_auto_20200603_1320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='countrypage',
            name='country',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='landmatrix.Country'),
        ),
    ]
