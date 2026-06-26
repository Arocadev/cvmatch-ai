from django.shortcuts import redirect
from django.conf import settings

RUTAS_EXCLUIDAS = ['/acceso/', '/static/', '/idioma/']

class PasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(ruta) for ruta in RUTAS_EXCLUIDAS):
            return self.get_response(request)
        
        if not request.session.get('acceso_validado'):
            return redirect('/acceso/')
        
        return self.get_response(request)