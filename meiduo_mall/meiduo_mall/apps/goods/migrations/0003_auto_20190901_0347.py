# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-09-01 03:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0002_goodsvisitcount'),
    ]

    operations = [
        migrations.AddField(
            model_name='goods',
            name='desc_detail',
            field=models.CharField(max_length=50, null=True, verbose_name='商品详情'),
        ),
        migrations.AddField(
            model_name='goods',
            name='desc_pack',
            field=models.CharField(max_length=50, null=True, verbose_name='规格与包装'),
        ),
        migrations.AddField(
            model_name='goods',
            name='desc_service',
            field=models.CharField(max_length=50, null=True, verbose_name='售后服务'),
        ),
    ]
