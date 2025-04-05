# Generated by Django 5.0.9 on 2025-04-04 23:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DisparadorApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='campanha',
            name='status',
            field=models.CharField(choices=[('agendada', 'Agendada'), ('ativa', 'Ativa'), ('finalizada', 'Finalizada')], default='agendada', max_length=20),
        ),
        migrations.AlterField(
            model_name='campanha',
            name='descricao',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='campanha',
            name='nome',
            field=models.CharField(max_length=255),
        ),
    ]
