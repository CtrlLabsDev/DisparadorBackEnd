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

    decoded_file = TextIOWrapper(arquivo.file, encoding="utf-8")
    reader = csv.DictReader(decoded_file, delimiter=';')

    count = 0
    for row in reader:
        telefone = row.get("telefone")
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
    agora = datetime.now()
    campanhas = Campanha.objects.filter(
        # status="emexecucao",
        data_inicio__lte=agora.date(),
        hora_inicio__lte=agora.time(),
        hora_termino__gte=agora.time()
    )

    mensagens = []

    for campanha in campanhas:
        dados = Dados.objects.filter(enviado=False, campanha=campanha)
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
    p.wait()  # Espera o processo terminar
    disparo_em_execucao = False

    try:
        campanha = Campanha.objects.get(id=campanha_id)
        campanha.status = 'finalizada'
        campanha.save()
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
        processo_disparo = subprocess.Popen(
            ['node', 'index.js'],
            cwd='C:/projetos/Disparador-Wpp/DisparadorBot'
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
        return Response({'erro': str(e)}, status=500)
