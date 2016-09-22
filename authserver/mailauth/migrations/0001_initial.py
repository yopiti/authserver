# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-22 09:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mailauth.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='MNUser',
            fields=[
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='Shareable ID')),
                ('identifier', models.CharField(db_index=True, max_length=255, unique=True, verbose_name='User ID')),
                ('fullname', models.CharField(max_length=255, verbose_name='Full name')),
                ('password', mailauth.models.PretendHasherPasswordField(max_length=128, verbose_name='Password')),
                ('pgp_key_id', models.CharField(blank=True, default='', max_length=64, verbose_name='PGP Key ID')),
                ('yubikey_serial', models.CharField(blank=True, default='', max_length=64, verbose_name='Yubikey Serial')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='Staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='Active')),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', mailauth.models.MNUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='EmailAlias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mailprefix', models.CharField(max_length=255, verbose_name='Mail prefix')),
                ('domain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mailauth.Domain', verbose_name='On domain')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Email aliases',
            },
        ),
        migrations.AddField(
            model_name='mnuser',
            name='delivery_mailbox',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='mailauth.EmailAlias'),
        ),
        migrations.AddField(
            model_name='mnuser',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='mnuser',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
        migrations.AlterUniqueTogether(
            name='emailalias',
            unique_together=set([('mailprefix', 'domain')]),
        ),
    ]
