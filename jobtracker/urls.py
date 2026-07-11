from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('cvmatch-admin/', admin.site.urls),
    path('', include('ofertas.urls')),
]