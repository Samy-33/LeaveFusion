# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-30 16:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0005_auto_20170830_1153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extrainfo',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]
