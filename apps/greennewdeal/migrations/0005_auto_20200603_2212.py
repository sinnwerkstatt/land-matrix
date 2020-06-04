# Generated by Django 2.2.12 on 2020-06-03 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('greennewdeal', '0004_auto_20200601_1353'),
    ]

    operations = [
        migrations.RenameField(
            model_name='location',
            old_name='geojson',
            new_name='areas',
        ),
        migrations.AddField(
            model_name='deal',
            name='draft_status',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (2, 'Review'), (3, 'Activation')], null=True),
        ),
        migrations.AddField(
            model_name='investor',
            name='draft_status',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (2, 'Review'), (3, 'Activation')], null=True),
        ),
        migrations.AlterField(
            model_name='deal',
            name='status',
            field=models.IntegerField(choices=[(1, 'Draft'), (2, 'Live'), (3, 'Updated'), (4, 'Deleted'), (5, 'Rejected'), (6, 'To Delete?')], default=1),
        ),
        migrations.AlterField(
            model_name='investor',
            name='status',
            field=models.IntegerField(choices=[(1, 'Draft'), (2, 'Live'), (3, 'Updated'), (4, 'Deleted'), (5, 'Rejected'), (6, 'To Delete?')], default=1),
        ),
    ]