# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-28 16:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eis', '0036_auto_20171028_0415'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emp_achievement',
            name='a_type',
            field=models.CharField(choices=[('Award', 'Award'), ('Honour', 'Honour'), ('Prize', 'Prize'), ('Other', 'Other')], default='Other', max_length=18),
        ),
    ]