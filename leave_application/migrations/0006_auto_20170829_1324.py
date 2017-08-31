# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-29 13:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave_application', '0005_leaverequest_timestamp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='leavescount',
            name='station',
        ),
        migrations.AlterField(
            model_name='leave',
            name='type_of_leave',
            field=models.CharField(choices=[('casual', 'Casual Leave'), ('restricted', 'Restricted Holidays'), ('vacation', 'Vacation Leave'), ('earned', 'Earned Leave'), ('special_casual', 'Special Casual Leave')], default='casual', max_length=20),
        ),
    ]
