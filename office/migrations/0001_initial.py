# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.CharField(help_text=b'drop and drag', max_length=1024, verbose_name='\u6587\u4ef6\u540d')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u751f\u6210\u65f6\u95f4')),
            ],
        ),
        migrations.CreateModel(
            name='BlockHole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('folder', models.CharField(unique=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Commit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u751f\u6210\u65f6\u95f4')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65f6\u95f4')),
                ('uid', models.CharField(max_length=255)),
                ('content', models.TextField(max_length=1024)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Distribution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u751f\u6210\u65f6\u95f4')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65f6\u95f4')),
                ('uid', models.CharField(max_length=255)),
                ('commit', models.OneToOneField(null=True, verbose_name=b'comment', to='office.Commit')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reference', models.CharField(null=True, default=None, max_length=32, blank=True, unique=True, verbose_name='\u6587\u53f7')),
                ('title', models.CharField(max_length=256, verbose_name='\u6587\u9898')),
                ('issue', models.CharField(max_length=128, verbose_name='\u53d1\u6587\u5355\u4f4d')),
                ('generated', models.DateField(default=django.utils.timezone.now, verbose_name='\u6210\u6587\u65f6\u95f4')),
                ('registered', models.DateField(default=django.utils.timezone.now, verbose_name='\u767b\u8bb0\u65f6\u95f4')),
                ('urgent', models.PositiveSmallIntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(0, '\u7d27\u6025'), (1, '\u666e\u901a'), (2, '\u65e0\u5173')])),
                ('note', models.TextField(max_length=512, null=True, verbose_name='\u5907\u6ce8', blank=True)),
                ('folder', models.CharField(default=None, max_length=512, null=True, blank=True)),
                ('repo_id', models.CharField(default=None, max_length=36, null=True, blank=True)),
            ],
            options={
                'verbose_name': '\u6587\u4ef6',
                'verbose_name_plural': '\u6587\u4ef6\u5939',
            },
        ),
        migrations.CreateModel(
            name='Info',
            fields=[
                ('key', models.CharField(max_length=32, serialize=False, primary_key=True)),
                ('value', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('symbol', models.CharField(max_length=32, serialize=False, primary_key=True)),
                ('organization', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u751f\u6210\u65f6\u95f4')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65f6\u95f4')),
                ('uid', models.CharField(max_length=255)),
                ('counter', models.IntegerField(default=1)),
                ('commit', models.OneToOneField(null=True, verbose_name=b'comment', to='office.Commit')),
                ('doc', models.ForeignKey(to='office.Document')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='distribution',
            name='doc',
            field=models.OneToOneField(to='office.Document'),
        ),
        migrations.AddField(
            model_name='commit',
            name='doc',
            field=models.ForeignKey(verbose_name=b'document', to='office.Document'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='doc',
            field=models.ForeignKey(to='office.Document'),
        ),
    ]
