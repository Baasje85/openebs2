# Generated by Django 2.2.9 on 2020-07-27 11:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('openebs', '0012_kv17mutationmessage_kv17shorten'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='kv17shorten',
            options={'permissions': (('view_change', 'Ritaanpassingen bekijken'), ('add_change', 'Ritaanpassingen aanmaken'), ('cancel_lines', 'Lijnen annuleren')), 'verbose_name': 'Ritverkorting', 'verbose_name_plural': 'Ritverkortingen'},
        ),
    ]
