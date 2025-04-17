import openpyxl
import csv
import io
import subprocess
import threading

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets
from .models import Campanha, Mensagem, Configuracao, Dados
from .serializers import CampanhaSerializer, MensagemSerializer, ConfiguracaoSerializer, DadosSerializer, ConfiguracaoSerializer
from django.http import HttpResponse
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser
from io import TextIOWrapper
from .tasks import disparar_mensagens
from datetime import datetime
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models.functions import TruncDate
from django.db.models import Count

import subprocess
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Campanha

#Variavel
disparo_em_execucao = False
processo_disparo = None

class CampanhaViewSet(viewsets.ModelViewSet):
    queryset = Campanha.objects.all().order_by('-data_criacao')
    serializer_class = CampanhaSerializer

    def update(self, request, *args, **kwargs):
        # Sempre que editar, altera o status para agendada
        request.data['status'] = 'agendada'
        return super().update(request, *args, **kwargs)



class MensagemViewSet(viewsets.ModelViewSet):
    queryset = Mensagem.objects.all().order_by('-id')
    serializer_class = MensagemSerializer


class ConfiguracaoViewSet(viewsets.ModelViewSet):
    queryset = Configuracao.objects.all()
    serializer_class = ConfiguracaoSerializer


class DadosViewSet(viewsets.ModelViewSet):
    queryset = Dados.objects.all()
    serializer_class = DadosSerializer


@api_view(['GET', 'POST', 'PUT'])
def unica_configuracao(request):
    config = Configuracao.objects.first()

    if request.method == 'GET':
        serializer = ConfiguracaoSerializer(config)
        return Response(serializer.data)

    if request.method == 'POST' and config is None:
        serializer = ConfiguracaoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    if request.method == 'PUT' and config:
        serializer = ConfiguracaoSerializer(config, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
def download_modelo_excel(request):
    # Cria o arquivo Excel em memória
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Modelo de Importação"

    # Cabeçalhos (em ordem)
    ws.append(["telefone", "variavel_a", "variavel_b", "variavel_c", "variavel_d"])

    # Define o tipo de resposta como arquivo Excel
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename=modelo_importacao.xlsx'

    # Salva o arquivo na resposta
    wb.save(response)
    return response



@api_view(['POST'])
def importar_csv_dados(request):
    arquivo = request.FILES.get("arquivo")
    campanha_id = request.POST.get("campanha_id")

    if not arquivo or not campanha_id:
        return Response({"erro": "Arquivo ou ID da campanha não enviado."}, status=400)

    decoded_file = TextIOWrapper(arquivo.file, encoding="utf-8", newline='')  # 👈 previne quebra errada de linha
    reader = csv.DictReader(decoded_file, delimiter=';', quotechar='"', skipinitialspace=True)  # 👈 trata espaços e campos compostos  

    count = 0
    for row in reader:
        telefone = row.get("telefone") or row.get("\ufefftelefone")
        if not telefone:
            print("Linha ignorada: telefone ausente", row)
            continue

        Dados.objects.create(
            telefone=telefone,
            variavel_a=row.get("variavel_a", ""),
            variavel_b=row.get("variavel_b", ""),
            variavel_c=row.get("variavel_c", ""),
            variavel_d=row.get("variavel_d", ""),
            enviado=False,
            campanha_id=campanha_id
        )
        count += 1

    return Response({"mensagem": f"{count} registros importados com sucesso."})


@api_view(["POST"])
def testar_disparo(request):
    disparar_mensagens()
    return Response({"mensagem": "Mensagens simuladas com sucesso!"})



@api_view(['GET'])
def buscar_mensagens_disparo(request):
    campanha_id = request.query_params.get("campanha_id")  # 👈 captura da URL
    if not campanha_id:
        return Response({"erro": "ID da campanha não informado."}, status=400)

    try:
        campanha = Campanha.objects.get(id=campanha_id)
    except Campanha.DoesNotExist:
        return Response({"erro": "Campanha não encontrada."}, status=404)

    dados = Dados.objects.filter(enviado=False, campanha_id=campanha_id)

    mensagens = []
    for dado in dados:
        mensagem_formatada = campanha.mensagem.format(
            variavel_a=dado.variavel_a or "",
            variavel_b=dado.variavel_b or "",
            variavel_c=dado.variavel_c or "",
            variavel_d=dado.variavel_d or "",
        )

        mensagens.append({
            "id": dado.id,
            "telefone": dado.telefone,
            "mensagem": mensagem_formatada,
            "campanha_id": campanha.id,
            "hora_inicio": str(campanha.hora_inicio),
            "hora_termino": str(campanha.hora_termino)
        })

    return Response(mensagens)





@api_view(['PATCH'])
def atualizar_status_envio(request, pk):
    try:
        dado = Dados.objects.get(pk=pk)
        dado.enviado = True
        dado.data_envio = datetime.now()

        # Se foi enviado um campo "erro_envio" = True no body
        if request.data.get("erro_envio"):
            dado.erro_envio = True

        dado.save()
        return Response({"mensagem": "Status atualizado com sucesso!"})
    except Dados.DoesNotExist:
        return Response({"erro": "Dado não encontrado."}, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET'])
def configuracao_envio(request):
    config = Configuracao.objects.first()
    if config:
        return Response({
            'min': config.periodo_envio_min,
            'max': config.periodo_envio_max
        })
    return Response({'erro': 'Nenhuma configuração encontrada.'}, status=404)



def monitorar_processo(p, campanha_id):
    global disparo_em_execucao
    p.wait()
    disparo_em_execucao = False

    try:
        campanha = Campanha.objects.get(id=campanha_id)

        # Só finaliza se o status ainda for em execução
        if campanha.status == 'emexecucao':
            campanha.status = 'finalizada'
            campanha.save()
            print(f"✅ Campanha ID {campanha_id} finalizada automaticamente.")
        else:
            print(f"⚠️ Campanha ID {campanha_id} não finalizada. Status atual: {campanha.status}")
    except Campanha.DoesNotExist:
        print("⚠️ Campanha não encontrada para finalizar.")

    print("🟢 Processo finalizado. Flag liberada.")




@api_view(['POST'])
def iniciar_disparo(request):
    global disparo_em_execucao, processo_disparo

    

    if disparo_em_execucao:
        return Response({'mensagem': 'Já existe um processo em execução.'}, status=409)

    campanha_id = request.data.get('campanha_id')
    if not campanha_id:
        return Response({'erro': 'ID da campanha não enviado'}, status=400)

    try:

        print("📨 Requisição recebida:", request.data)
        print("📌 Tentando iniciar campanha ID:", campanha_id)

         # Busca a campanha
        campanha = get_object_or_404(Campanha, id=campanha_id)

         # Valida status permitido
        if campanha.status not in ['agendada', 'pausada']:
            return Response({'erro': 'Campanha não pode ser iniciada. Status atual: ' + campanha.status}, status=400)

         # Inicia subprocesso
        processo_disparo = subprocess.Popen(
            ['node', 'index.js', str(campanha_id)],
            cwd='/home/alphabeto/CtrLabs/DisparadorBOT'
        )
        disparo_em_execucao = True


        # Atualiza status para "emexecucao"
        campanha = get_object_or_404(Campanha, id=campanha_id)
        campanha.status = 'emexecucao'
        campanha.save()

        # Inicia monitoramento em background
        threading.Thread(target=monitorar_processo, args=(processo_disparo, campanha_id)).start()

        return Response({'mensagem': 'Processo de disparo iniciado com sucesso.'})
    except Exception as e:
        disparo_em_execucao = False
        print("❌ Erro ao iniciar disparo:", str(e))  # 👈 ESSENCIAL PRA VER O ERRO
        return Response({'erro': str(e)}, status=500)




@api_view(['GET'])
def dashboard_kpis(request):
    total = Dados.objects.count()
    enviadas = Dados.objects.filter(enviado=True).count()
    aguardando = Dados.objects.filter(enviado=False).count()
    com_erro = Dados.objects.filter(enviado=True, erro_envio=True).count()

    return Response({
        "total": total,
        "enviadas": enviadas,
        "aguardando": aguardando,
        "com_erro": com_erro
    })


@api_view(['GET'])
def grafico_mensagens_por_dia(request):
    dados = Dados.objects.filter(enviado=True).annotate(
        data=TruncDate("data_envio")
    ).values("data").annotate(
        total=Count("id")
    ).order_by("data")

    labels = [d["data"].strftime("%d/%m/%Y") for d in dados]
    valores = [d["total"] for d in dados]

    return Response({
        "labels": labels,
        "valores": valores
    })



@api_view(['PATCH'])
def registrar_erro_envio(request, pk):
    try:
        dado = Dados.objects.get(pk=pk)
        erro = request.data.get('erro', '')
        dado.erro_envio = erro
        dado.save()
        return Response({"mensagem": "Erro registrado com sucesso!"})
    except Dados.DoesNotExist:
        return Response({"erro": "Dado não encontrado."}, status=status.HTTP_404_NOT_FOUND)




# Usa o logger da app (ajuste o nome se quiser, ex: 'django', 'disparo' etc.)
logger = logging.getLogger(__name__)

@api_view(['POST'])
def parar_disparo(request):
    campanha_id = request.data.get("campanha_id")
    logger.info("========== POST /parar-disparo ==========")
    logger.info(f"campanha_id recebida: {campanha_id}")

    try:
        # Tenta matar o processo 'node index.js'
        logger.info("Executando: pkill -f 'node index.js'")
        subprocess.run(['pkill', '-f', 'node index.js'], check=False)

        # Verifica se ainda há algum processo ativo
        logger.info("Executando verificação: ps aux | grep '[n]ode index.js'")
        result = subprocess.run(
            "ps aux | grep '[n]ode index.js'",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        output = result.stdout.strip()
        if output:
            logger.warning("Processo ainda ativo após pkill:")
            logger.warning(output)
            return Response({'mensagem': 'Erro: processo ainda em execução.'}, status=500)

        # Atualiza status da campanha no banco de dados
        if campanha_id:
            campanha = get_object_or_404(Campanha, id=campanha_id)
            campanha.status = 'pausada'
            campanha.save()
            logger.info(f"Campanha ID {campanha_id} atualizada para status 'pausada'.")

        logger.info("Campanha pausada com sucesso.")
        logger.info("========== Fim /parar-disparo ==========\n")
        return Response({'mensagem': 'Campanha pausada com sucesso.'}, status=200)

    except Exception as e:
        logger.exception("Erro ao tentar pausar a campanha:")
        return Response({'erro': str(e)}, status=500)   