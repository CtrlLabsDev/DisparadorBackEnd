# Generated by Django 5.0.9 on 2025-04-04 23:47

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DisparadorApp', '0002_campanha_status_alter_campanha_descricao_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='campanha',
            name='hora_inicio',
            field=models.TimeField(default=datetime.time(8, 0)),
        ),
        migrations.AddField(
            model_name='campanha',
            name='hora_termino',
            field=models.TimeField(default=datetime.time(18, 0)),
        ),
        migrations.AddField(
            model_name='campanha',
            name='mensagem',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='campanha',
            name='data_inicio',
            field=models.DateField(),
        ),
    ]
