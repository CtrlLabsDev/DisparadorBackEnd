import openpyxl
import csv
import io

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets
from .models import Campanha, Mensagem, Configuracao, Dados
from .serializers import CampanhaSerializer, MensagemSerializer, ConfiguracaoSerializer, DadosSerializer
from django.http import HttpResponse
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser
from io import TextIOWrapper
from .tasks import disparar_mensagens


class CampanhaViewSet(viewsets.ModelViewSet):
    queryset = Campanha.objects.all().order_by('-data_criacao')
    serializer_class = CampanhaSerializer


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