from django.shortcuts import render
from .models import Oferta
from django.shortcuts import render, get_object_or_404
import os

def lista_ofertas(request):
    ofertas = Oferta.objects.all().order_by('-fecha_guardada')
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas})

def detalle_oferta(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    return render(request, 'ofertas/detalle.html', {'oferta': oferta})

def analizar_cv(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    
    if request.method == 'POST':
        cv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cv.txt')
        with open(cv_path, 'r', encoding='utf-8') as f:
            cv_texto = f.read()
        
        from .cv import analizar_oferta_para_cv
        analisis = analizar_oferta_para_cv(oferta.descripcion, cv_texto)
        
        return render(request, 'ofertas/analisis.html', {
            'oferta': oferta,
            'analisis': analisis
        })
    
    return render(request, 'ofertas/analisis.html', {'oferta': oferta})