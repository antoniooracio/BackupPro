# Generated by Django 4.2.16 on 2024-11-07 20:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_manufacturer'),
    ]

    operations = [
        migrations.RenameField(
            model_name='manufacturer',
            old_name='Nome',
            new_name='nome',
        ),
    ]