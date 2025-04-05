# DisparadorApp/tasks.py

import random
import time
from datetime import datetime
from .models import Dados, Campanha


def enviar_whatsapp(telefone, mensagem):
    print(f"Enviando para {telefone}: {mensagem}")
    # Aqui entra a lógica com Puppeteer ou Selenium no futuro
    return True  # Simula envio bem-sucedido


def disparar_mensagens():
    agora = datetime.now()
    campanhas = Campanha.objects.filter(
        status="agendada",
        data_inicio__lte=agora.date(),
        hora_inicio__lte=agora.time(),
        hora_termino__gte=agora.time()
    )

    for campanha in campanhas:
        dados = Dados.objects.filter(enviado=False, campanha=campanha)

        for dado in dados:
            mensagem_formatada = campanha.mensagem.format(
                variavel_a=dado.variavel_a or "",
                variavel_b=dado.variavel_b or "",
                variavel_c=dado.variavel_c or "",
                variavel_d=dado.variavel_d or "",
            )

            sucesso = enviar_whatsapp(dado.telefone, mensagem_formatada)

            if sucesso:
                dado.enviado = True
                dado.data_envio = agora
                dado.save()

            time.sleep(random.uniform(3, 8))  # Delay para simular envio humano
