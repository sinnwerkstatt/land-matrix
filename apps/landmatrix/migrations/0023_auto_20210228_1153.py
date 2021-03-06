# Generated by Django 2.2.17 on 2021-02-28 10:53

import apps.landmatrix.models.deal
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('landmatrix', '0022_auto_20210127_1158'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deal',
            old_name='current_resources',
            new_name='current_mineral_resources',
        ),
        migrations.RenameField(
            model_name='deal',
            old_name='resources',
            new_name='mineral_resources',
        ),
        migrations.RenameField(
            model_name='deal',
            old_name='resources_comment',
            new_name='mineral_resources_comment',
        ),
        migrations.AlterField(
            model_name='deal',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deals', to='landmatrix.Country', verbose_name='Target country'),
        ),
        migrations.AlterField(
            model_name='deal',
            name='current_intention_of_investment',
            field=apps.landmatrix.models.deal.ArrayField(base_field=models.CharField(max_length=100), blank=True, choices=[('Agriculture', (('BIOFUELS', 'Biofuels'), ('FOOD_CROPS', 'Food crops'), ('FODDER', 'Fodder'), ('LIVESTOCK', 'Livestock'), ('NON_FOOD_AGRICULTURE', 'Non-food agricultural commodities'), ('AGRICULTURE_UNSPECIFIED', 'Agriculture unspecified'))), ('Forestry', (('TIMBER_PLANTATION', 'Timber plantation'), ('FOREST_LOGGING', 'Forest logging / management'), ('CARBON', 'For carbon sequestration/REDD'), ('FORESTRY_UNSPECIFIED', 'Forestry unspecified'))), ('Other', (('MINING', 'Mining'), ('OIL_GAS_EXTRACTION', 'Oil / Gas extraction'), ('TOURISM', 'Tourism'), ('INDUSTRY', 'Industry'), ('CONVERSATION', 'Conservation'), ('LAND_SPECULATION', 'Land speculation'), ('RENEWABLE_ENERGY', 'Renewable energy'), ('OTHER', 'Other')))], null=True, size=None),
        ),
        migrations.AlterField(
            model_name='deal',
            name='intention_of_investment',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, choices=[('Agriculture', (('BIOFUELS', 'Biofuels'), ('FOOD_CROPS', 'Food crops'), ('FODDER', 'Fodder'), ('LIVESTOCK', 'Livestock'), ('NON_FOOD_AGRICULTURE', 'Non-food agricultural commodities'), ('AGRICULTURE_UNSPECIFIED', 'Agriculture unspecified'))), ('Forestry', (('TIMBER_PLANTATION', 'Timber plantation'), ('FOREST_LOGGING', 'Forest logging / management'), ('CARBON', 'For carbon sequestration/REDD'), ('FORESTRY_UNSPECIFIED', 'Forestry unspecified'))), ('Other', (('MINING', 'Mining'), ('OIL_GAS_EXTRACTION', 'Oil / Gas extraction'), ('TOURISM', 'Tourism'), ('INDUSTRY', 'Industry'), ('CONVERSATION', 'Conservation'), ('LAND_SPECULATION', 'Land speculation'), ('RENEWABLE_ENERGY', 'Renewable energy'), ('OTHER', 'Other')))], null=True, verbose_name='Intention of investment'),
        ),
        migrations.AlterField(
            model_name='deal',
            name='involved_actors',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, choices=[('GOVERNMENT_OR_STATE_INSTITUTIONS', 'Government / state institutions (government, ministries, departments, agencies etc.)'), ('TRADITIONAL_LAND_OWNERS_OR_COMMUNITIES', 'Traditional land-owners / communities'), ('TRADITIONAL_LOCAL_AUTHORITY', 'Traditional local authority (e.g. Chiefdom council / Chiefs)'), ('BROKER', 'Broker'), ('INTERMEDIARY', 'Intermediary'), ('OTHER', 'Other (please specify)')], null=True, verbose_name='Actors involved in the negotiation / admission process'),
        ),
        migrations.AlterField(
            model_name='deal',
            name='materialized_benefits',
            field=apps.landmatrix.models.deal.ArrayField(base_field=models.CharField(max_length=100, verbose_name='Materialized benefits for local communities'), blank=True, choices=[('HEALTH', 'Health'), ('EDUCATION', 'Education'), ('PRODUCTIVE_INFRASTRUCTURE', 'Productive infrastructure (e.g. irrigation, tractors, machinery...)'), ('ROADS', 'Roads'), ('CAPACITY_BUILDING', 'Capacity building'), ('FINANCIAL_SUPPORT', 'Financial support'), ('COMMUNITY_SHARES', 'Community shares in the investment project'), ('OTHER', 'Other')], null=True, size=None),
        ),
        migrations.AlterField(
            model_name='deal',
            name='nature_of_deal',
            field=apps.landmatrix.models.deal.ArrayField(base_field=models.CharField(max_length=100, verbose_name='Nature of the deal'), blank=True, choices=[('OUTRIGHT_PURCHASE', 'Outright purchase'), ('LEASE', 'Lease'), ('CONCESSION', 'Concession'), ('EXPLOITATION_PERMIT', 'Exploitation permit / license / concession (for mineral resources)'), ('PURE_CONTRACT_FARMING', 'Pure contract farming'), ('OTHER', 'Other')], null=True, size=None),
        ),
        migrations.AlterField(
            model_name='deal',
            name='not_public_reason',
            field=models.CharField(blank=True, choices=[('CONFIDENTIAL', 'Confidential flag'), ('NO_COUNTRY', 'No country'), ('HIGH_INCOME_COUNTRY', 'High-income country'), ('NO_DATASOURCES', 'No datasources'), ('NO_OPERATING_COMPANY', 'No operating company'), ('NO_KNOWN_INVESTOR', 'No known investor')], max_length=100),
        ),
        migrations.AlterField(
            model_name='deal',
            name='promised_benefits',
            field=apps.landmatrix.models.deal.ArrayField(base_field=models.CharField(max_length=100, verbose_name='Promised benefits for local communities'), blank=True, choices=[('HEALTH', 'Health'), ('EDUCATION', 'Education'), ('PRODUCTIVE_INFRASTRUCTURE', 'Productive infrastructure (e.g. irrigation, tractors, machinery...)'), ('ROADS', 'Roads'), ('CAPACITY_BUILDING', 'Capacity building'), ('FINANCIAL_SUPPORT', 'Financial support'), ('COMMUNITY_SHARES', 'Community shares in the investment project'), ('OTHER', 'Other')], null=True, size=None),
        ),
    ]
