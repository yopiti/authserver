# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-01 15:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dockerauth', '0004_find_domains_for_registries'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dockerregistry',
            name='sign_key',
        ),
    ]
