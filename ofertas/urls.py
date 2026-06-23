from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_ofertas, name='lista_ofertas'),
    path('<int:pk>/', views.detalle_oferta, name='detalle_oferta'),
    path('<int:pk>/analizar/', views.analizar_cv, name='analizar_cv'),
]