from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('DisparadorApp.urls')),  # Nome correto do aplicativo
]