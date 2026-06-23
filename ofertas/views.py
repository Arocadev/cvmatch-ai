from django.shortcuts import render, get_object_or_404, redirect
from .models import Oferta
from .api import buscar_ofertas
from pypdf import PdfReader
from datetime import datetime
import os
import io

def lista_ofertas(request):
    if request.session.get('buscar_ahora'):
        keywords = request.session.get('keywords', 'devops')
        ubicacion = request.session.get('ubicacion', 'Valencia')
        
        resultado = buscar_ofertas(keywords=keywords, ubicacion=ubicacion)
        ofertas_api = resultado.get('results', [])
        
        for item in ofertas_api:
            oferta_id = item.get('id')
            if not Oferta.objects.filter(url_original__contains=oferta_id).exists():
                Oferta.objects.create(
                    titulo=item.get('title', ''),
                    empresa=item['company'].get('display_name', ''),
                    ubicacion=item['location'].get('display_name', ''),
                    descripcion=item.get('description', ''),
                    url_original=item.get('redirect_url', ''),
                    fecha_publicacion=datetime.strptime(
                        item['created'][:10], '%Y-%m-%d'
                    ).date(),
                    estado='nueva',
                    fuente='adzuna',
                )
        
        request.session['buscar_ahora'] = False
    
    ofertas = Oferta.objects.filter(estado='nueva').order_by('-fecha_guardada')
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas})

def ofertas_guardadas(request):
    ofertas = Oferta.objects.filter(estado='guardada').order_by('-fecha_guardada')
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas})

def ofertas_descartadas(request):
    ofertas = Oferta.objects.filter(estado='descartada').order_by('-fecha_guardada')
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas})

def cambiar_estado(request, pk, estado):
    oferta = get_object_or_404(Oferta, pk=pk)
    oferta.estado = estado
    oferta.save()
    return redirect(request.META.get('HTTP_REFERER', 'lista_ofertas'))

def detalle_oferta(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    return render(request, 'ofertas/detalle.html', {'oferta': oferta})

def analizar_cv(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    
    if request.method == 'POST':
        cv_texto = request.session.get('cv_texto', None)
        
        if not cv_texto:
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

def configuracion(request):
    if request.method == 'POST':
        keywords = request.POST.get('keywords', 'devops')
        ubicacion = request.POST.get('ubicacion', 'Valencia')
        
        if 'cv_pdf' in request.FILES:
            pdf_file = request.FILES['cv_pdf']
            reader = PdfReader(io.BytesIO(pdf_file.read()))
            cv_texto = ''
            for page in reader.pages:
                cv_texto += page.extract_text()
            request.session['cv_texto'] = cv_texto
        
        request.session['keywords'] = keywords
        request.session['ubicacion'] = ubicacion
        request.session['buscar_ahora'] = True
        
        return redirect('lista_ofertas')
    
    return render(request, 'ofertas/configuracion.html')