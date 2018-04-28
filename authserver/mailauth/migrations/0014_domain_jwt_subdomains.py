# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-03-31 12:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailauth', '0013_merge_20180331_1208'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='jwt_subdomains',
            field=models.BooleanField(default=False, verbose_name='Use JWT key to sign for subdomains'),
        ),
    ]
