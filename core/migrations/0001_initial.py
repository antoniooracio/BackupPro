# Generated by Django 4.2.16 on 2024-11-07 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='enterprise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome da empresa')),
                ('uf', models.CharField(max_length=2, verbose_name='Estado')),
                ('cidade', models.CharField(max_length=100, verbose_name='Cidade')),
                ('endereco', models.CharField(max_length=400, verbose_name='Endereço')),
                ('cnpj', models.CharField(max_length=18, verbose_name='CNPJ')),
                ('representante', models.CharField(max_length=50, verbose_name='Nome do representante')),
                ('contato', models.CharField(max_length=12, verbose_name='Telefone')),
            ],
        ),
    ]