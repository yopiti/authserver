# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-03-13 00:16
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mailauth.models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('mailauth', '0010_domain_redirect_to'),
    ]

    operations = [
        migrations.CreateModel(
            name='MNServiceUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(default=uuid.uuid4, max_length=64, verbose_name='Username')),
                ('password', mailauth.models.PretendHasherPasswordField(max_length=128, verbose_name='Password')),
                ('description', models.CharField(blank=True, default='', max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Service User',
                'verbose_name_plural': 'Service Users',
            },
            bases=(mailauth.models.PasswordMaskMixin, models.Model),
        ),
    ]
