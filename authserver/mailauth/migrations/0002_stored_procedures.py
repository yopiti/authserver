# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-21 21:57
from __future__ import unicode_literals

from typing import List

from django.db import migrations
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):

    dependencies = [
        ('mailauth', '0001_initial'),
    ]

    # This migration previously installed the stored procedure API in the database.
    # It has been replaced by the 'spapi' management.py command.

    operations = [
    ]  # type: List[Operation]
