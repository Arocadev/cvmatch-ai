from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Oferta
from .api import buscar_ofertas
from datetime import datetime
import pdfplumber
import os
import io

def lista_ofertas(request):
    if request.session.get('buscar_ahora'):
        Oferta.objects.filter(estado='nueva').delete()
        
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

    todas = Oferta.objects.filter(estado='nueva').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    pagina = request.GET.get('page', 1)
    ofertas = paginator.get_page(pagina)
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas, 'seccion': 'nuevas'})

def ofertas_vistas(request):
    todas = Oferta.objects.filter(estado='vista').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    pagina = request.GET.get('page', 1)
    ofertas = paginator.get_page(pagina)
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas, 'seccion': 'vistas'})

def ofertas_guardadas(request):
    todas = Oferta.objects.filter(estado='guardada').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    pagina = request.GET.get('page', 1)
    ofertas = paginator.get_page(pagina)
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas, 'seccion': 'guardadas'})

def ofertas_descartadas(request):
    todas = Oferta.objects.filter(estado='descartada').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    pagina = request.GET.get('page', 1)
    ofertas = paginator.get_page(pagina)
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas, 'seccion': 'descartadas'})

def cambiar_estado(request, pk, estado):
    oferta = get_object_or_404(Oferta, pk=pk)
    oferta.estado = estado
    oferta.save()
    return redirect(request.META.get('HTTP_REFERER', 'lista_ofertas'))

def detalle_oferta(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    if oferta.estado == 'nueva':
        oferta.estado = 'vista'
        oferta.save()
    return render(request, 'ofertas/detalle.html', {'oferta': oferta})

def analizar_cv(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    
    if request.method == 'POST':
        cv_texto = ''

        if 'cv_pdf' in request.FILES and request.FILES['cv_pdf'].size > 0:
            pdf_file = request.FILES['cv_pdf']
            pdf_bytes = pdf_file.read()
            from .cv import extraer_texto_pdf
            cv_texto = extraer_texto_pdf(pdf_bytes)

        if not cv_texto:
            cv_texto = request.POST.get('cv_texto_manual', '').strip()

        if cv_texto:
            request.session['cv_texto'] = cv_texto
            request.session.modified = True

        if not cv_texto:
            cv_texto = request.session.get('cv_texto', None)

        if not cv_texto:
            return render(request, 'ofertas/analisis.html', {
                'oferta': oferta,
                'error': 'Necesitas introducir tu CV primero.',
                'cv_subido': False,
                'cv_texto_guardado': ''
            })
        
        from .cv import analizar_oferta_para_cv
        analisis = analizar_oferta_para_cv(oferta.descripcion, cv_texto)
        
        return render(request, 'ofertas/analisis.html', {
            'oferta': oferta,
            'analisis': analisis,
            'cv_subido': True,
            'cv_texto_guardado': cv_texto
        })
    
    cv_texto_guardado = request.session.get('cv_texto', '')
    cv_subido = bool(cv_texto_guardado)
    return render(request, 'ofertas/analisis.html', {
        'oferta': oferta,
        'cv_subido': cv_subido,
        'cv_texto_guardado': cv_texto_guardado
    })

def configuracion(request):
    if request.method == 'POST':
        keywords = request.POST.get('keywords', '').strip()
        ubicacion = request.POST.get('ubicacion', '').strip()

        request.session['keywords'] = keywords
        request.session['ubicacion'] = ubicacion
        request.session['buscar_ahora'] = True
        request.session.modified = True
        
        return redirect('lista_ofertas')
    
    return render(request, 'ofertas/configuracion.html')