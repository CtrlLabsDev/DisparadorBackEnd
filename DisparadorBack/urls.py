from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('DisparadorApp.urls')),  # 👈 adiciona aqui
    path('', include('DisparadorApp.urls')),
]
