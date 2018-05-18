# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('office', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='document',
            options={'verbose_name': '\u6587\u4ef6', 'verbose_name_plural': '\u6587\u4ef6'},
        ),
        migrations.AlterField(
            model_name='blockhole',
            name='folder',
            field=models.CharField(unique=True, max_length=128),
        ),
        migrations.AlterField(
            model_name='document',
            name='folder',
            field=models.CharField(default=None, max_length=128, null=True, blank=True),
        ),
    ]
