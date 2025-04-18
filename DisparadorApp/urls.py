from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampanhaViewSet, MensagemViewSet, ConfiguracaoViewSet, DadosViewSet
from .views import download_modelo_excel, importar_csv_dados, testar_disparo, buscar_mensagens_disparo, atualizar_status_envio, unica_configuracao, iniciar_disparo
from . import views
from .views import dashboard_kpis, parar_disparo, registrar_erro_envio


router = DefaultRouter()
router.register(r'campanhas', CampanhaViewSet)
router.register(r'mensagens', MensagemViewSet)
router.register(r'configuracoes', ConfiguracaoViewSet)
router.register(r'dados', DadosViewSet)  

urlpatterns = [
    path('', include(router.urls)),
    path('importar-csv-dados/', importar_csv_dados, name='importar_csv_dados'),
    path("testar-disparo/", testar_disparo),
    path('buscar-mensagens-disparo/', buscar_mensagens_disparo, name='buscar_mensagens_disparo'),
    path('api/atualizar-status-envio/<int:pk>/', atualizar_status_envio),
    path('unica-configuracao/', unica_configuracao, name='unica-configuracao'),
    path('api/iniciar-disparo/', iniciar_disparo, name='iniciar_disparo'),
    path('dashboard-kpis/', views.dashboard_kpis),
    path('api/mensagens-por-dia/', views.grafico_mensagens_por_dia),
    path('api/registrar-erro-envio/<int:pk>/', views.registrar_erro_envio),
    path('api/parar-disparo/', views.parar_disparo),

]

urlpatterns += [
    path('download-modelo-excel/', download_modelo_excel, name='download_modelo_excel'),
]
