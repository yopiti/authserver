# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-20 02:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailauth', '0003_opensmtpd_access'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='dkimkey',
            field=models.TextField(blank=True, verbose_name='DKIM private key (PEM)'),
        ),
    ]