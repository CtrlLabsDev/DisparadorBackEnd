from django.db import models
from datetime import time



class Campanha(models.Model):
    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('emexecucao', 'Em Execução'),
        ('finalizada', 'Finalizada'),
    ]

    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    mensagem = models.TextField(default='', null=True)  # ✅ default vazio para facilitar migração
    data_inicio = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(default=time(8, 0), blank=True, null=True)  # ✅ Default: 08:00
    hora_termino = models.TimeField(default=time(18, 0), blank=True, null=True)  # ✅ Default: 18:00
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='agendada', blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Mensagem(models.Model):
    campanha = models.ForeignKey(Campanha, on_delete=models.CASCADE, related_name="mensagens")
    telefone = models.CharField(max_length=20)
    variavel_a = models.CharField(max_length=255, blank=True)
    variavel_b = models.CharField(max_length=255, blank=True)
    enviada = models.BooleanField(default=False)
    data_envio = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.telefone} - {self.campanha.nome}"


class Configuracao(models.Model):
    numero_whatsapp = models.CharField(max_length=20)
    periodo_envio_min = models.IntegerField(help_text="Período mínimo entre mensagens (min)")
    periodo_envio_max = models.IntegerField(help_text="Período máximo entre mensagens (min)")


    def __str__(self):
        return f"Configuração de {self.numero_whatsapp}"



class Dados(models.Model):
    telefone = models.CharField(max_length=20)
    variavel_a = models.CharField(max_length=255, blank=True, null=True)
    variavel_b = models.CharField(max_length=255, blank=True, null=True)
    variavel_c = models.CharField(max_length=255, blank=True, null=True)
    variavel_d = models.CharField(max_length=255, blank=True, null=True)
    enviado = models.BooleanField(default=False)
    data_envio = models.DateTimeField(blank=True, null=True)
    campanha = models.ForeignKey("Campanha", on_delete=models.CASCADE, related_name="dados")
    erro_envio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.telefone