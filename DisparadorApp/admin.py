from django.contrib import admin
from .models import Campanha, Mensagem, Configuracao, Dados

# Register your models here.



class CampanhaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'nome', 'descricao', 'mensagem', 'data_inicio',
        'hora_inicio', 'hora_termino', 'status', 'data_criacao'
    )


admin.site.register(Campanha, CampanhaAdmin)



admin.site.register(Mensagem)
admin.site.register(Configuracao)
admin.site.register(Dados)