# Generated by Django 2.2.17 on 2020-12-30 09:38

import apps.blog.abstract
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_squashed_0006_auto_20180206_2239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpage',
            name='author',
            field=models.ForeignKey(blank=True, limit_choices_to=apps.blog.abstract.limit_author_choices, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='author_pages', to=settings.AUTH_USER_MODEL, verbose_name='Author'),
        ),
        migrations.AlterField(
            model_name='blogpage',
            name='blog_categories',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, through='blog.BlogCategoryBlogPage', to='blog.BlogCategory'),
        ),
    ]
