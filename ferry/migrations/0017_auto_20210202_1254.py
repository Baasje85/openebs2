# Generated by Django 2.2.17 on 2021-02-02 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ferry', '0016_auto_20160424_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ferrykv6messages',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Gereed voor vertrek'), (5, 'Vertrokken'), (10, 'Aankomst')], default=0, verbose_name='Status'),
        ),
    ]