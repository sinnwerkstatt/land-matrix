# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-07-26 18:34
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('landmatrix', '0008_auto_20180119_2250'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalInvestorActivityInvolvement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Timestamp')),
                ('fk_activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='landmatrix.HistoricalActivity', verbose_name='Activity')),
            ],
            options={
                'verbose_name_plural': 'Historical Investor Activity Involvements',
                'get_latest_by': 'timestamp',
                'verbose_name': 'Historical Investor Activity Involvement',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalInvestorVentureInvolvement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ST', 'Parent company'), ('IN', 'Tertiary investor/lendor')], max_length=2, verbose_name='Relation type')),
                ('investment_type', multiselectfield.db.fields.MultiSelectField(blank=True, choices=[(10, 'Shares/Equity'), (20, 'Debt financing')], default='', max_length=255, null=True)),
                ('percentage', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)], verbose_name='Ownership share')),
                ('loans_amount', models.FloatField(blank=True, null=True, verbose_name='Loan amount')),
                ('loans_date', models.CharField(blank=True, max_length=10, null=True, verbose_name='Loan date')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Comment')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Timestamp')),
            ],
            options={
                'verbose_name_plural': 'Historical Investor Venture Involvements',
                'get_latest_by': 'timestamp',
                'verbose_name': 'Historical Investor Venture Involvement',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddField(
            model_name='historicalinvestorventureinvolvement',
            name='fk_investor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='investors', to='landmatrix.HistoricalInvestor', verbose_name='Investor ID Upstream'),
        ),
        migrations.AddField(
            model_name='historicalinvestorventureinvolvement',
            name='fk_status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='landmatrix.Status', verbose_name='Status'),
        ),
        migrations.AddField(
            model_name='historicalinvestorventureinvolvement',
            name='fk_venture',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='venture_involvements', to='landmatrix.HistoricalInvestor', verbose_name='Investor ID Downstream'),
        ),
        migrations.AddField(
            model_name='historicalinvestorventureinvolvement',
            name='loans_currency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='landmatrix.Currency', verbose_name='Loan currency'),
        ),
        migrations.AddField(
            model_name='historicalinvestoractivityinvolvement',
            name='fk_investor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='landmatrix.HistoricalInvestor', verbose_name='Investor'),
        ),
        migrations.AddField(
            model_name='historicalinvestoractivityinvolvement',
            name='fk_status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='landmatrix.Status', verbose_name='Status'),
        ),
    ]
