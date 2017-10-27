# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-07 16:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eis', '0005_auto_20171007_2212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emp_research_papers',
            name='authors',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='emp_research_papers',
            name='is_sci',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=1),
        ),
        migrations.AlterField(
            model_name='emp_research_papers',
            name='name_journal',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='emp_research_papers',
            name='status',
            field=models.CharField(blank=True, choices=[('Published', 'Published'), ('Accepted', 'Accepted'), ('Communicated', 'Communicated')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='emp_research_papers',
            name='title_paper',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]