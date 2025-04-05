from rest_framework import serializers
from .models import Campanha, Mensagem, Configuracao, Dados


class CampanhaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campanha
        fields = '__all__'


class MensagemSerializer(serializers.ModelSerializer):
    campanha_nome = serializers.CharField(source='campanha.nome', read_only=True)

    class Meta:
        model = Mensagem
        fields = '__all__'


class ConfiguracaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuracao
        fields = '__all__'


class DadosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dados
        fields = '__all__'
