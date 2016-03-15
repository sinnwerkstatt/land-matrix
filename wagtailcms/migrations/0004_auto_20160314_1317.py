# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailcore.fields
import wagtail.wagtailcore.blocks
import wagtail.wagtailembeds.blocks
import wagtail.wagtailimages.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcms', '0003_auto_20160314_1316'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wagtailpage',
            name='body',
            field=wagtail.wagtailcore.fields.StreamField((('heading', wagtail.wagtailcore.blocks.CharBlock(classname='full title')), ('paragraph', wagtail.wagtailcore.blocks.RichTextBlock()), ('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('media', wagtail.wagtailembeds.blocks.EmbedBlock()), ('link', wagtail.wagtailcore.blocks.URLBlock()), ('columns_1_1', wagtail.wagtailcore.blocks.StructBlock((('left_column', wagtail.wagtailcore.blocks.StreamBlock((('heading', wagtail.wagtailcore.blocks.CharBlock(classname='full title')), ('paragraph', wagtail.wagtailcore.blocks.RichTextBlock()), ('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('media', wagtail.wagtailembeds.blocks.EmbedBlock()), ('link', wagtail.wagtailcore.blocks.URLBlock())))), ('right_column', wagtail.wagtailcore.blocks.StreamBlock((('heading', wagtail.wagtailcore.blocks.CharBlock(classname='full title')), ('paragraph', wagtail.wagtailcore.blocks.RichTextBlock()), ('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('media', wagtail.wagtailembeds.blocks.EmbedBlock()), ('link', wagtail.wagtailcore.blocks.URLBlock())), form_classname='pull-right'))))))),
        ),
    ]
