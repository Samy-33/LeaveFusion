# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-27 13:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leave_application', '0002_auto_20170827_1247'),
    ]

    operations = [
        migrations.RenameField(
            model_name='leavescount',
            old_name='vacation_leaves',
            new_name='vacation',
        ),
    ]
