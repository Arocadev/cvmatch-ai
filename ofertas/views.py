from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Oferta
from .api import buscar_ofertas
from datetime import datetime
from django.conf import settings
import fitz
import os
import io

def get_idioma(request):
    return request.session.get('idioma', 'es')

def acceso(request):
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if password == settings.APP_PASSWORD:
            request.session['acceso_validado'] = True
            return redirect('inicio')
        else:
            return render(request, 'ofertas/acceso.html', {'error': 'Contraseña incorrecta'})
    return render(request, 'ofertas/acceso.html')

def inicio(request):
    return render(request, 'ofertas/inicio.html', {'idioma': get_idioma(request)})

def lista_ofertas(request):
    if request.session.get('buscar_ahora'):
        Oferta.objects.filter(estado='nueva').delete()
        
        keywords = request.session.get('keywords', 'devops')
        ubicacion = request.session.get('ubicacion', 'Valencia')
        fuente = request.session.get('fuente', 'adzuna_es')
        modalidad = request.session.get('modalidad', '')
        experiencia = request.session.get('experiencia', '')
        salario_min = request.session.get('salario_min', '')
        
        resultados = buscar_ofertas(
            keywords=keywords,
            ubicacion=ubicacion,
            fuente=fuente,
            salary_min=salario_min if salario_min else None,
        )
        
        for item in resultados:
            try:
                if fuente in ('adzuna_es', 'adzuna_uk', 'adzuna_us'):
                    oferta_id = item.get('id', '')
                    titulo = item.get('title', '')
                    empresa = item.get('company', {}).get('display_name', '')
                    ubicacion_oferta = item.get('location', {}).get('display_name', '')
                    descripcion = item.get('description', '')
                    url_original = item.get('redirect_url', '')
                    fecha = datetime.strptime(item['created'][:10], '%Y-%m-%d').date()
                    fuente_nombre = fuente

                elif fuente == 'jooble':
                    oferta_id = str(item.get('id', ''))
                    titulo = item.get('title', '')
                    empresa = item.get('company', '')
                    ubicacion_oferta = item.get('location', '')
                    descripcion = item.get('snippet', '')
                    url_original = item.get('link', '')
                    fecha_str = item.get('updated', '')[:10]
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.now().date()
                    fuente_nombre = 'jooble'

                elif fuente == 'arbeitnow':
                    oferta_id = item.get('slug', '')
                    titulo = item.get('title', '')
                    empresa = item.get('company_name', '')
                    ubicacion_oferta = item.get('location', '')
                    descripcion = item.get('description', '')
                    url_original = item.get('url', '')
                    timestamp = item.get('created_at', 0)
                    fecha = datetime.fromtimestamp(timestamp).date() if timestamp else datetime.now().date()
                    fuente_nombre = 'arbeitnow'

                elif fuente == 'todas':
                    oferta_id = item.get('id', item.get('slug', ''))
                    titulo = item.get('titulo', '')
                    empresa = item.get('empresa', '')
                    ubicacion_oferta = item.get('ubicacion', '')
                    descripcion = item.get('descripcion', '')
                    url_original = item.get('url_original', '')
                    fecha = item.get('fecha', datetime.now().date())
                    fuente_nombre = item.get('fuente', 'desconocida')

                else:
                    continue

                desc_lower = descripcion.lower()
                if modalidad == 'remoto' and 'remoto' not in desc_lower and 'remote' not in desc_lower:
                    continue
                if modalidad == 'hibrido' and 'híbrido' not in desc_lower and 'hibrido' not in desc_lower and 'hybrid' not in desc_lower:
                    continue
                if modalidad == 'presencial' and 'presencial' not in desc_lower:
                    continue
                if experiencia in ('0', '1') and any(x in desc_lower for x in ['3 años', '4 años', '5 años', 'senior']):
                    continue
                if experiencia == '2' and any(x in desc_lower for x in ['4 años', '5 años', 'senior']):
                    continue

                if oferta_id and not Oferta.objects.filter(url_original__contains=oferta_id).exists():
                    Oferta.objects.create(
                        titulo=titulo,
                        empresa=empresa,
                        ubicacion=ubicacion_oferta,
                        descripcion=descripcion,
                        url_original=url_original,
                        fecha_publicacion=fecha,
                        estado='nueva',
                        fuente=fuente_nombre,
                    )
            except Exception as e:
                print(f"Error procesando oferta: {e}")
                continue

        request.session['buscar_ahora'] = False

    todas = Oferta.objects.filter(estado='nueva').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    pagina = request.GET.get('page', 1)
    ofertas = paginator.get_page(pagina)

    contadores = {
        'nuevas': Oferta.objects.filter(estado='nueva').count(),
        'vistas': Oferta.objects.filter(estado='vista').count(),
        'guardadas': Oferta.objects.filter(estado='guardada').count(),
        'descartadas': Oferta.objects.filter(estado='descartada').count(),
    }

    busqueda_activa = {
        'keywords': request.session.get('keywords', ''),
        'ubicacion': request.session.get('ubicacion', ''),
        'fuente': request.session.get('fuente', 'adzuna_es'),
    }

    return render(request, 'ofertas/lista.html', {
        'ofertas': ofertas,
        'seccion': 'nuevas',
        'contadores': contadores,
        'busqueda_activa': busqueda_activa,
        'idioma': get_idioma(request),
    })

def ofertas_vistas(request):
    todas = Oferta.objects.filter(estado='vista').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    pagina = request.GET.get('page', 1)
    ofertas = paginator.get_page(pagina)
    contadores = {
        'nuevas': Oferta.objects.filter(estado='nueva').count(),
        'vistas': Oferta.objects.filter(estado='vista').count(),
        'guardadas': Oferta.objects.filter(estado='guardada').count(),
        'descartadas': Oferta.objects.filter(estado='descartada').count(),
    }
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas, 'seccion': 'vistas', 'contadores': contadores, 'idioma': get_idioma(request)})

def ofertas_guardadas(request):
    todas = Oferta.objects.filter(estado='guardada').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    pagina = request.GET.get('page', 1)
    ofertas = paginator.get_page(pagina)
    contadores = {
        'nuevas': Oferta.objects.filter(estado='nueva').count(),
        'vistas': Oferta.objects.filter(estado='vista').count(),
        'guardadas': Oferta.objects.filter(estado='guardada').count(),
        'descartadas': Oferta.objects.filter(estado='descartada').count(),
    }
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas, 'seccion': 'guardadas', 'contadores': contadores, 'idioma': get_idioma(request)})

def ofertas_descartadas(request):
    todas = Oferta.objects.filter(estado='descartada').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    pagina = request.GET.get('page', 1)
    ofertas = paginator.get_page(pagina)
    contadores = {
        'nuevas': Oferta.objects.filter(estado='nueva').count(),
        'vistas': Oferta.objects.filter(estado='vista').count(),
        'guardadas': Oferta.objects.filter(estado='guardada').count(),
        'descartadas': Oferta.objects.filter(estado='descartada').count(),
    }
    return render(request, 'ofertas/lista.html', {'ofertas': ofertas, 'seccion': 'descartadas', 'contadores': contadores, 'idioma': get_idioma(request)})

def cambiar_estado(request, pk, estado):
    oferta = get_object_or_404(Oferta, pk=pk)
    oferta.estado = estado
    oferta.save()
    return redirect(request.META.get('HTTP_REFERER', 'lista_ofertas'))

def eliminar_ofertas(request):
    if request.method == 'POST':
        ids = request.POST.getlist('ofertas_ids')
        if ids:
            Oferta.objects.filter(id__in=ids).delete()
    return redirect('ofertas_descartadas')

def detalle_oferta(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    if oferta.estado == 'nueva':
        oferta.estado = 'vista'
        oferta.save()
    
    from .cv import resumir_oferta
    resumen = resumir_oferta(oferta.descripcion, get_idioma(request))
    
    return render(request, 'ofertas/detalle.html', {
        'oferta': oferta,
        'resumen': resumen,
        'idioma': get_idioma(request),
    })

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
                'error': 'Necesitas introducir tu CV primero.' if get_idioma(request) == 'es' else 'You need to upload your CV first.',
                'cv_subido': False,
                'cv_texto_guardado': '',
                'idioma': get_idioma(request),
            })
        
        from .cv import analizar_oferta_para_cv
        analisis = analizar_oferta_para_cv(oferta.descripcion, cv_texto, get_idioma(request))
        
        return render(request, 'ofertas/analisis.html', {
            'oferta': oferta,
            'analisis': analisis,
            'cv_subido': True,
            'cv_texto_guardado': cv_texto,
            'idioma': get_idioma(request),
        })
    
    cv_texto_guardado = request.session.get('cv_texto', '')
    cv_subido = bool(cv_texto_guardado)
    return render(request, 'ofertas/analisis.html', {
        'oferta': oferta,
        'cv_subido': cv_subido,
        'cv_texto_guardado': cv_texto_guardado,
        'idioma': get_idioma(request),
    })

def generar_cv(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    
    cv_texto = request.session.get('cv_texto', None)
    
    if not cv_texto:
        return redirect('analizar_cv', pk=pk)
    
    from .cv import generar_cv_adaptado
    cv_generado = generar_cv_adaptado(oferta.descripcion, cv_texto, get_idioma(request))
    
    return render(request, 'ofertas/cv_generado.html', {
        'oferta': oferta,
        'cv_generado': cv_generado,
        'idioma': get_idioma(request),
    })

def buscador(request):
    if request.method == 'POST':
        keywords = request.POST.get('keywords', '').strip()
        ubicacion = request.POST.get('ubicacion', '').strip()
        modalidad = request.POST.get('modalidad', '')
        experiencia = request.POST.get('experiencia', '')
        salario_min = request.POST.get('salario_min', '')
        fuente = request.POST.get('fuente', 'adzuna_es')

        request.session['keywords'] = keywords
        request.session['ubicacion'] = ubicacion
        request.session['modalidad'] = modalidad
        request.session['experiencia'] = experiencia
        request.session['salario_min'] = salario_min
        request.session['fuente'] = fuente
        request.session['buscar_ahora'] = True
        request.session.modified = True
        
        return redirect('lista_ofertas')
    
    return render(request, 'ofertas/buscador.html', {'idioma': get_idioma(request)})

def cambiar_idioma(request, idioma):
    request.session['idioma'] = idioma
    return redirect(request.META.get('HTTP_REFERER', 'inicio'))