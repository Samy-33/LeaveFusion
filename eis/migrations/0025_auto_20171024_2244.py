# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-24 17:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eis', '0024_auto_20171010_1909'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emp_expert_lectures',
            name='l_type',
            field=models.CharField(blank=True, choices=[('Expert Lecture', 'Expert Lecture'), ('Invited Talk', 'Invited Talk')], max_length=14, null=True),
        ),
    ]