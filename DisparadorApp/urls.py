from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampanhaViewSet, MensagemViewSet, ConfiguracaoViewSet, DadosViewSet, download_modelo_excel, importar_csv_dados, testar_disparo

router = DefaultRouter()
router.register(r'campanhas', CampanhaViewSet)
router.register(r'mensagens', MensagemViewSet)
router.register(r'configuracoes', ConfiguracaoViewSet)
router.register(r'dados', DadosViewSet)  

urlpatterns = [
    path('', include(router.urls)),
    path('importar-csv-dados/', importar_csv_dados, name='importar_csv_dados'),
    path("testar-disparo/", testar_disparo),
]

urlpatterns += [
    path('download-modelo-excel/', download_modelo_excel, name='download_modelo_excel'),
]
