from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/',    views.login_view,   name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/',   views.logout_view,  name='logout'),

    # Perfil
    path('perfil/',                      views.perfil,           name='perfil'),
    path('perfil/cambiar-password/',     views.cambiar_password, name='cambiar_password'),
    path('perfil/cv/subir/',             views.subir_cv,         name='subir_cv'),
    path('perfil/cv/<int:pk>/eliminar/', views.eliminar_cv,      name='eliminar_cv'),

    # App
    path('',                 views.inicio,       name='inicio'),
    path('buscador/',        views.buscador,     name='buscador'),
    path('ofertas/',         views.lista_ofertas,       name='lista_ofertas'),
    path('ofertas/vistas/',      views.ofertas_vistas,      name='ofertas_vistas'),
    path('ofertas/guardadas/',   views.ofertas_guardadas,   name='ofertas_guardadas'),
    path('ofertas/descartadas/', views.ofertas_descartadas, name='ofertas_descartadas'),
    path('ofertas/eliminar/',    views.eliminar_ofertas,    name='eliminar_ofertas'),

    # Detalle y acciones
    path('ofertas/<int:pk>/',                     views.detalle_oferta, name='detalle_oferta'),
    path('ofertas/<int:pk>/resumen-ia/',          views.resumen_ia,     name='resumen_ia'),
    path('tarea/<str:task_id>/status/',           views.resumen_ia_status, name='resumen_ia_status'),
    path('ofertas/<int:pk>/analizar/',            views.analizar_cv,    name='analizar_cv'),
    path('ofertas/<int:pk>/estado/<str:estado>/', views.cambiar_estado, name='cambiar_estado'),
    path('ofertas/<int:pk>/generar-cv/',          views.generar_cv,     name='generar_cv'),
    path('ofertas/<int:pk>/pdf/',                 views.descargar_pdf,  name='descargar_pdf'),
    path('ofertas/<int:pk>/panel-pdf/',           views.panel_pdf,      name='panel_pdf'),

    # Crear CV independiente
    path('crear-cv/',         views.crear_cv,           name='crear_cv'),
    path('crear-cv/mejorar/', views.mejorar_cv_ia,      name='mejorar_cv_ia'),
    path('crear-cv/pdf/',     views.descargar_pdf_libre, name='descargar_pdf_libre'),

    # Idioma y legal
    path('idioma/<str:idioma>/', views.cambiar_idioma, name='cambiar_idioma'),
    path('legal/',      views.legal,      name='legal'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('faq/',        views.faq,        name='faq'),
]