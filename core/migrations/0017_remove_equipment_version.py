# Generated by Django 4.2.16 on 2024-11-27 18:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_remove_equipment_horariobackup_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='equipment',
            name='version',
        ),
    ]
