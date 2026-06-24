from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('buscador/', views.buscador, name='buscador'),
    path('ofertas/', views.lista_ofertas, name='lista_ofertas'),
    path('ofertas/vistas/', views.ofertas_vistas, name='ofertas_vistas'),
    path('ofertas/guardadas/', views.ofertas_guardadas, name='ofertas_guardadas'),
    path('ofertas/descartadas/', views.ofertas_descartadas, name='ofertas_descartadas'),
    path('ofertas/eliminar/', views.eliminar_ofertas, name='eliminar_ofertas'),
    path('ofertas/<int:pk>/', views.detalle_oferta, name='detalle_oferta'),
    path('ofertas/<int:pk>/analizar/', views.analizar_cv, name='analizar_cv'),
    path('ofertas/<int:pk>/estado/<str:estado>/', views.cambiar_estado, name='cambiar_estado'),
    path('ofertas/<int:pk>/generar-cv/', views.generar_cv, name='generar_cv'),
]