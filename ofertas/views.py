from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Oferta, UserProfile, CVUsuario
from .api import buscar_ofertas
from .security import (rate_limit, validar_pdf, validar_imagen,
                        sanitizar_texto, sanitizar_busqueda, sanitizar_prompt)
from datetime import datetime
import logging
import os
import tempfile
import markdown as md

logger = logging.getLogger('seguridad')


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_idioma(request):
    return request.session.get('idioma', 'es')

def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile

def get_contadores(user):
    return {
        'nuevas':      Oferta.objects.filter(usuario=user, estado='nueva').count(),
        'vistas':      Oferta.objects.filter(usuario=user, estado='vista').count(),
        'guardadas':   Oferta.objects.filter(usuario=user, estado='guardada').count(),
        'descartadas': Oferta.objects.filter(usuario=user, estado='descartada').count(),
    }

def render_md(texto):
    return md.markdown(texto, extensions=['nl2br'])

def _get_groq_token(request) -> str | None:
    """Devuelve el token Groq del usuario o None (usa el global del .env)."""
    profile = get_or_create_profile(request.user)
    return profile.get_groq_token()

def _texto_es_en(es: str, en: str, idioma: str) -> str:
    return es if idioma == 'es' else en


# ─── Auth ─────────────────────────────────────────────────────────────────────

@rate_limit('login', limite=10, periodo=300)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    error = None
    if request.method == 'POST':
        username = sanitizar_texto(request.POST.get('username', ''), max_length=150).strip()
        password = request.POST.get('password', '')
        if not username or not password:
            error = _texto_es_en('Rellena todos los campos.', 'Fill in all fields.', get_idioma(request))
        else:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect(request.GET.get('next', 'inicio'))
            else:
                logger.warning(f'Login fallido — usuario: {username} — IP: {request.META.get("REMOTE_ADDR")}')
                error = _texto_es_en(
                    'Usuario o contraseña incorrectos.',
                    'Invalid username or password.',
                    get_idioma(request)
                )
    return render(request, 'ofertas/login.html', {'error': error, 'idioma': get_idioma(request)})


@rate_limit('registro', limite=5, periodo=3600)
def registro_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    error = None
    if request.method == 'POST':
        username = sanitizar_texto(request.POST.get('username', ''), max_length=150).strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if not username or not password1:
            error = _texto_es_en('Rellena todos los campos.', 'Fill in all fields.', get_idioma(request))
        elif password1 != password2:
            error = _texto_es_en('Las contraseñas no coinciden.', 'Passwords do not match.', get_idioma(request))
        elif User.objects.filter(username=username).exists():
            error = _texto_es_en('Ese nombre de usuario ya está en uso.', 'That username is already taken.', get_idioma(request))
        elif len(password1) < 8:
            error = _texto_es_en('La contraseña debe tener al menos 8 caracteres.', 'Password must be at least 8 characters.', get_idioma(request))
        else:
            user = User.objects.create_user(username=username, password=password1)
            get_or_create_profile(user)
            login(request, user)
            return redirect('inicio')
    return render(request, 'ofertas/registro.html', {'error': error, 'idioma': get_idioma(request)})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Perfil ───────────────────────────────────────────────────────────────────

@login_required
def perfil(request):
    profile = get_or_create_profile(request.user)
    cvs = CVUsuario.objects.filter(usuario=request.user)
    puede_añadir_cv = cvs.count() < 3
    mensaje = None
    error = None

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'foto':
            if 'foto' in request.FILES:
                archivo = request.FILES['foto']
                valido, error_msg = validar_imagen(archivo)
                if not valido:
                    error = error_msg
                else:
                    profile.foto = archivo.read()
                    profile.foto_mime = archivo.content_type or 'image/jpeg'
                    profile.save()
                    mensaje = _texto_es_en('Foto actualizada correctamente.', 'Photo updated successfully.', get_idioma(request))

        elif accion == 'groq_token':
            token = request.POST.get('groq_token', '').strip()
            if token and not token.startswith('gsk_'):
                error = _texto_es_en(
                    'El token de Groq debe empezar por gsk_.',
                    'Groq token must start with gsk_.',
                    get_idioma(request)
                )
            else:
                profile.set_groq_token(token)
                profile.save()
                mensaje = _texto_es_en(
                    'Token Groq guardado correctamente.' if token else 'Token Groq eliminado.',
                    'Groq token saved.' if token else 'Groq token removed.',
                    get_idioma(request)
                )

    return render(request, 'ofertas/perfil.html', {
        'profile': profile,
        'cvs': cvs,
        'puede_añadir_cv': puede_añadir_cv,
        'mensaje': mensaje,
        'error': error,
        'idioma': get_idioma(request),
    })


@login_required
def cambiar_password(request):
    error = None
    mensaje = None
    if request.method == 'POST':
        password_actual = request.POST.get('password_actual', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if not request.user.check_password(password_actual):
            error = _texto_es_en('La contraseña actual no es correcta.', 'Current password is incorrect.', get_idioma(request))
        elif password1 != password2:
            error = _texto_es_en('Las contraseñas nuevas no coinciden.', 'New passwords do not match.', get_idioma(request))
        elif len(password1) < 8:
            error = _texto_es_en('La contraseña debe tener al menos 8 caracteres.', 'Password must be at least 8 characters.', get_idioma(request))
        else:
            request.user.set_password(password1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            mensaje = _texto_es_en('Contraseña cambiada correctamente.', 'Password updated successfully.', get_idioma(request))
    return render(request, 'ofertas/cambiar_password.html', {
        'error': error, 'mensaje': mensaje, 'idioma': get_idioma(request),
    })


@login_required
def subir_cv(request):
    if request.method == 'POST':
        if CVUsuario.objects.filter(usuario=request.user).count() >= 3:
            return redirect('perfil')
        nombre = sanitizar_texto(request.POST.get('nombre', ''), max_length=100).strip()
        cv_texto = ''
        if 'cv_pdf' in request.FILES and request.FILES['cv_pdf'].size > 0:
            archivo = request.FILES['cv_pdf']
            valido, error_msg = validar_pdf(archivo)
            if not valido:
                cvs = CVUsuario.objects.filter(usuario=request.user)
                return render(request, 'ofertas/perfil.html', {
                    'profile': get_or_create_profile(request.user),
                    'cvs': cvs,
                    'puede_añadir_cv': cvs.count() < 3,
                    'error': error_msg,
                    'idioma': get_idioma(request),
                })
            pdf_bytes = archivo.read()
            from .cv import extraer_texto_pdf
            cv_texto = extraer_texto_pdf(pdf_bytes)
        if not cv_texto:
            cv_texto = sanitizar_texto(request.POST.get('cv_texto', ''), max_length=50000).strip()
        if nombre and cv_texto:
            CVUsuario.objects.create(usuario=request.user, nombre=nombre, texto=cv_texto)
    return redirect('perfil')


@login_required
def eliminar_cv(request, pk):
    cv = get_object_or_404(CVUsuario, pk=pk, usuario=request.user)
    cv.delete()
    return redirect('perfil')


# ─── App ──────────────────────────────────────────────────────────────────────

@login_required
def inicio(request):
    return render(request, 'ofertas/inicio.html', {'idioma': get_idioma(request)})


@login_required
@rate_limit('buscador', limite=30, periodo=3600)
def buscador(request):
    if request.method == 'POST':
        request.session['keywords'] = sanitizar_busqueda(request.POST.get('keywords', ''))
        request.session['ubicacion'] = sanitizar_busqueda(request.POST.get('ubicacion', ''))
        request.session['modalidad'] = request.POST.get('modalidad', '')
        request.session['experiencia'] = request.POST.get('experiencia', '')
        request.session['salario_min'] = request.POST.get('salario_min', '')
        fuente = request.POST.get('fuente', 'adzuna_es')
        if fuente not in ('adzuna_es', 'adzuna_uk', 'adzuna_us', 'jooble', 'arbeitnow', 'todas'):
            fuente = 'adzuna_es'
        request.session['fuente'] = fuente
        request.session['buscar_ahora'] = True
        request.session.modified = True
        return redirect('lista_ofertas')
    return render(request, 'ofertas/buscador.html', {'idioma': get_idioma(request)})


@login_required
def lista_ofertas(request):
    if request.session.get('buscar_ahora'):
        Oferta.objects.filter(usuario=request.user, estado='nueva').delete()
        keywords    = request.session.get('keywords', 'devops')
        ubicacion   = request.session.get('ubicacion', 'Valencia')
        fuente      = request.session.get('fuente', 'adzuna_es')
        modalidad   = request.session.get('modalidad', '')
        experiencia = request.session.get('experiencia', '')
        salario_min = request.session.get('salario_min', '')
        resultados  = buscar_ofertas(
            keywords=keywords, ubicacion=ubicacion, fuente=fuente,
            salary_min=salario_min if salario_min else None,
        )
        for item in resultados:
            try:
                if fuente in ('adzuna_es', 'adzuna_uk', 'adzuna_us'):
                    oferta_id        = item.get('id', '')
                    titulo           = item.get('title', '')
                    empresa          = item.get('company', {}).get('display_name', '')
                    ubicacion_oferta = item.get('location', {}).get('display_name', '')
                    descripcion      = item.get('description', '')
                    url_original     = item.get('redirect_url', '')
                    fecha            = datetime.strptime(item['created'][:10], '%Y-%m-%d').date()
                    fuente_nombre    = fuente
                elif fuente == 'jooble':
                    oferta_id        = str(item.get('id', ''))
                    titulo           = item.get('title', '')
                    empresa          = item.get('company', '')
                    ubicacion_oferta = item.get('location', '')
                    descripcion      = item.get('snippet', '')
                    url_original     = item.get('link', '')
                    fecha_str        = item.get('updated', '')[:10]
                    fecha            = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.now().date()
                    fuente_nombre    = 'jooble'
                elif fuente == 'arbeitnow':
                    oferta_id        = item.get('slug', '')
                    titulo           = item.get('title', '')
                    empresa          = item.get('company_name', '')
                    ubicacion_oferta = item.get('location', '')
                    descripcion      = item.get('description', '')
                    url_original     = item.get('url', '')
                    timestamp        = item.get('created_at', 0)
                    fecha            = datetime.fromtimestamp(timestamp).date() if timestamp else datetime.now().date()
                    fuente_nombre    = 'arbeitnow'
                elif fuente == 'todas':
                    oferta_id        = item.get('id', item.get('slug', ''))
                    titulo           = item.get('titulo', '')
                    empresa          = item.get('empresa', '')
                    ubicacion_oferta = item.get('ubicacion', '')
                    descripcion      = item.get('descripcion', '')
                    url_original     = item.get('url_original', '')
                    fecha            = item.get('fecha', datetime.now().date())
                    fuente_nombre    = item.get('fuente', 'desconocida')
                else:
                    continue

                desc_lower = descripcion.lower()
                if modalidad == 'remoto' and 'remoto' not in desc_lower and 'remote' not in desc_lower:
                    continue
                if modalidad == 'hibrido' and not any(x in desc_lower for x in ['híbrido', 'hibrido', 'hybrid']):
                    continue
                if modalidad == 'presencial' and 'presencial' not in desc_lower:
                    continue
                if experiencia in ('0', '1') and any(x in desc_lower for x in ['3 años', '4 años', '5 años', 'senior']):
                    continue
                if experiencia == '2' and any(x in desc_lower for x in ['4 años', '5 años', 'senior']):
                    continue

                if oferta_id and not Oferta.objects.filter(usuario=request.user, url_original__contains=oferta_id).exists():
                    Oferta.objects.create(
                        usuario=request.user, titulo=titulo, empresa=empresa,
                        ubicacion=ubicacion_oferta, descripcion=descripcion,
                        url_original=url_original, fecha_publicacion=fecha,
                        estado='nueva', fuente=fuente_nombre,
                    )
            except Exception as e:
                logger.error(f'Error procesando oferta: {e}')
                continue
        request.session['buscar_ahora'] = False

    todas = Oferta.objects.filter(usuario=request.user, estado='nueva').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    ofertas = paginator.get_page(request.GET.get('page', 1))
    busqueda_activa = {
        'keywords': request.session.get('keywords', ''),
        'ubicacion': request.session.get('ubicacion', ''),
        'fuente':    request.session.get('fuente', 'adzuna_es'),
    }
    return render(request, 'ofertas/lista.html', {
        'ofertas': ofertas, 'seccion': 'nuevas',
        'contadores': get_contadores(request.user),
        'busqueda_activa': busqueda_activa,
        'idioma': get_idioma(request),
    })


@login_required
def ofertas_vistas(request):
    todas = Oferta.objects.filter(usuario=request.user, estado='vista').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    ofertas = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'ofertas/lista.html', {
        'ofertas': ofertas, 'seccion': 'vistas',
        'contadores': get_contadores(request.user), 'idioma': get_idioma(request),
    })


@login_required
def ofertas_guardadas(request):
    todas = Oferta.objects.filter(usuario=request.user, estado='guardada').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    ofertas = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'ofertas/lista.html', {
        'ofertas': ofertas, 'seccion': 'guardadas',
        'contadores': get_contadores(request.user), 'idioma': get_idioma(request),
    })


@login_required
def ofertas_descartadas(request):
    todas = Oferta.objects.filter(usuario=request.user, estado='descartada').order_by('-fecha_guardada')
    paginator = Paginator(todas, 10)
    ofertas = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'ofertas/lista.html', {
        'ofertas': ofertas, 'seccion': 'descartadas',
        'contadores': get_contadores(request.user), 'idioma': get_idioma(request),
    })


@login_required
def cambiar_estado(request, pk, estado):
    ESTADOS_VALIDOS = ('nueva', 'vista', 'guardada', 'descartada')
    if estado not in ESTADOS_VALIDOS:
        return redirect('lista_ofertas')
    oferta = get_object_or_404(Oferta, pk=pk, usuario=request.user)
    oferta.estado = estado
    oferta.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'estado': estado})
    return redirect(request.META.get('HTTP_REFERER', 'lista_ofertas'))


@login_required
def eliminar_ofertas(request):
    if request.method == 'POST':
        ids = request.POST.getlist('ofertas_ids')
        if ids:
            Oferta.objects.filter(id__in=ids, usuario=request.user).delete()
    return redirect('ofertas_descartadas')


# ─── Detalle oferta ───────────────────────────────────────────────────────────

@login_required
def detalle_oferta(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk, usuario=request.user)
    if oferta.estado == 'nueva':
        oferta.estado = 'vista'
        oferta.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'id':               oferta.pk,
            'titulo':           oferta.titulo,
            'empresa':          oferta.empresa,
            'ubicacion':        oferta.ubicacion,
            'descripcion':      oferta.descripcion,
            'url_original':     oferta.url_original,
            'fecha_publicacion': oferta.fecha_publicacion.isoformat() if oferta.fecha_publicacion else '',
            'estado':           oferta.estado,
            'fuente':           oferta.fuente,
            'resumen_ia':       oferta.resumen_ia or '',
        })

    return render(request, 'ofertas/detalle.html', {
        'oferta': oferta,
        'idioma': get_idioma(request),
        'contadores': get_contadores(request.user),
    })


# ─── Resumen IA manual ────────────────────────────────────────────────────────

@login_required
@require_POST
@rate_limit('resumen_ia', limite=20, periodo=3600)
def resumen_ia(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk, usuario=request.user)

    if oferta.resumen_ia:
        return JsonResponse({'status': 'cached', 'html': oferta.resumen_ia})

    token = _get_groq_token(request)

    try:
        from .tasks import task_resumir_oferta
        task = task_resumir_oferta.delay(oferta.pk, get_idioma(request), token)
        return JsonResponse({'status': 'pending', 'task_id': task.id})
    except Exception:
        # Fallback síncrono si Celery no está disponible
        from .cv import resumir_oferta as _resumir
        try:
            resumen_raw = _resumir(
                sanitizar_prompt(oferta.descripcion, max_length=8000),
                get_idioma(request),
                token=token,
            )
            html = render_md(resumen_raw)
            oferta.resumen_ia = html
            oferta.save(update_fields=['resumen_ia'])
            return JsonResponse({'status': 'ok', 'html': html})
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=500)


@login_required
def resumen_ia_status(request, task_id):
    from celery.result import AsyncResult
    result = AsyncResult(task_id)
    if result.ready():
        data = result.get(timeout=1)
        html = data.get('html', '') if data.get('status') == 'ok' else ''
        return JsonResponse({'status': 'ok', 'html': html})
    return JsonResponse({'status': 'pending'})


# ─── Análisis CV ──────────────────────────────────────────────────────────────

@login_required
@rate_limit('analisis', limite=20, periodo=3600)
def analizar_cv(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk, usuario=request.user)
    cvs_usuario = CVUsuario.objects.filter(usuario=request.user)

    if request.method == 'POST':
        cv_texto = ''
        cv_id = request.POST.get('cv_id')
        if cv_id:
            try:
                cv_obj = CVUsuario.objects.get(pk=cv_id, usuario=request.user)
                cv_texto = cv_obj.texto
            except CVUsuario.DoesNotExist:
                pass
        if not cv_texto and 'cv_pdf' in request.FILES and request.FILES['cv_pdf'].size > 0:
            archivo = request.FILES['cv_pdf']
            valido, error_msg = validar_pdf(archivo)
            if not valido:
                return render(request, 'ofertas/analisis.html', {
                    'oferta': oferta, 'cvs_usuario': cvs_usuario,
                    'error': error_msg, 'idioma': get_idioma(request),
                })
            pdf_bytes = archivo.read()
            from .cv import extraer_texto_pdf
            cv_texto = extraer_texto_pdf(pdf_bytes)
        if not cv_texto:
            cv_texto = sanitizar_texto(request.POST.get('cv_texto_manual', ''), max_length=50000).strip()
        if not cv_texto:
            return render(request, 'ofertas/analisis.html', {
                'oferta': oferta, 'cvs_usuario': cvs_usuario,
                'error': _texto_es_en(
                    'Selecciona o introduce tu CV primero.',
                    'Select or enter your CV first.',
                    get_idioma(request)
                ),
                'idioma': get_idioma(request),
            })

        token = _get_groq_token(request)
        from .cv import analizar_oferta_para_cv
        try:
            analisis = render_md(analizar_oferta_para_cv(
                sanitizar_prompt(oferta.descripcion, max_length=8000),
                sanitizar_prompt(cv_texto, max_length=20000),
                get_idioma(request),
                token=token,
            ))
        except Exception as e:
            return render(request, 'ofertas/analisis.html', {
                'oferta': oferta, 'cvs_usuario': cvs_usuario,
                'error': str(e), 'idioma': get_idioma(request),
            })
        request.session['cv_texto'] = cv_texto
        request.session.modified = True
        return render(request, 'ofertas/analisis.html', {
            'oferta': oferta, 'cvs_usuario': cvs_usuario,
            'analisis': analisis, 'cv_subido': True,
            'cv_texto_guardado': cv_texto, 'idioma': get_idioma(request),
        })

    cv_texto_guardado = request.session.get('cv_texto', '')
    return render(request, 'ofertas/analisis.html', {
        'oferta': oferta, 'cvs_usuario': cvs_usuario,
        'cv_subido': bool(cv_texto_guardado),
        'cv_texto_guardado': cv_texto_guardado,
        'idioma': get_idioma(request),
    })


# ─── Generar CV ───────────────────────────────────────────────────────────────

@login_required
def generar_cv(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk, usuario=request.user)
    cv_texto = request.session.get('cv_texto')
    if not cv_texto:
        return redirect('analizar_cv', pk=pk)

    token = _get_groq_token(request)
    from .cv import generar_cv_adaptado
    try:
        cv_generado_raw = generar_cv_adaptado(
            sanitizar_prompt(oferta.descripcion, max_length=8000),
            sanitizar_prompt(cv_texto, max_length=20000),
            get_idioma(request),
            token=token,
        )
    except Exception as e:
        return render(request, 'ofertas/analisis.html', {
            'oferta': oferta,
            'cvs_usuario': CVUsuario.objects.filter(usuario=request.user),
            'error': str(e),
            'idioma': get_idioma(request),
        })

    cv_generado_html = render_md(cv_generado_raw)
    return render(request, 'ofertas/cv_generado.html', {
        'oferta': oferta,
        'cv_generado': cv_generado_html,
        'cv_generado_raw': cv_generado_raw,
        'idioma': get_idioma(request),
    })


# ─── PDF ──────────────────────────────────────────────────────────────────────

@login_required
def panel_pdf(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk, usuario=request.user)
    profile = get_or_create_profile(request.user)
    return render(request, 'ofertas/panel_pdf.html', {
        'oferta': oferta, 'profile': profile, 'idioma': get_idioma(request),
    })


@login_required
def descargar_pdf(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk, usuario=request.user)
    profile = get_or_create_profile(request.user)
    if request.method != 'POST':
        return redirect('generar_cv', pk=pk)

    plantilla = request.POST.get('plantilla', 'profesional')
    if plantilla not in ('neutra', 'profesional', 'moderna'):
        plantilla = 'profesional'

    modo          = request.POST.get('modo', 'automatico')
    nombre        = sanitizar_texto(request.POST.get('nombre', request.user.username), max_length=100)
    subtitulo     = sanitizar_texto(request.POST.get('subtitulo', ''), max_length=200)
    email         = sanitizar_texto(request.POST.get('email', ''), max_length=100)
    telefono      = sanitizar_texto(request.POST.get('telefono', ''), max_length=30)
    linkedin      = sanitizar_texto(request.POST.get('linkedin', ''), max_length=150)
    ubicacion_pdf = sanitizar_texto(request.POST.get('ubicacion', ''), max_length=100)
    opcion_foto   = request.POST.get('opcion_foto', 'ninguna')

    cv_texto = sanitizar_texto(request.POST.get('cv_manual', ''), max_length=50000).strip() if modo == 'manual' else request.session.get('cv_texto', '')

    if not cv_texto:
        return redirect('generar_cv', pk=pk)

    foto_path = None
    if opcion_foto == 'perfil' and profile.foto:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        tmp.write(bytes(profile.foto))
        tmp.close()
        foto_path = tmp.name

    from .pdf import generar_pdf as gen_pdf
    datos = {
        'nombre': nombre, 'subtitulo': subtitulo,
        'email': email, 'telefono': telefono,
        'linkedin': linkedin, 'ubicacion': ubicacion_pdf,
    }
    buffer = gen_pdf(datos, cv_texto, plantilla=plantilla, foto_path=foto_path)

    if foto_path:
        try:
            os.unlink(foto_path)
        except Exception:
            pass

    nombre_archivo = f"CV_{nombre.replace(' ', '_')}_{oferta.titulo.replace(' ', '_')[:20]}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response


# ─── Idioma ───────────────────────────────────────────────────────────────────

def cambiar_idioma(request, idioma):
    if idioma in ('es', 'en'):
        request.session['idioma'] = idioma
    return redirect(request.META.get('HTTP_REFERER', 'inicio'))


# ─── Legal ────────────────────────────────────────────────────────────────────

def legal(request):
    return render(request, 'ofertas/legal.html', {'idioma': get_idioma(request)})

def privacidad(request):
    return render(request, 'ofertas/privacidad.html', {'idioma': get_idioma(request)})

def faq(request):
    return render(request, 'ofertas/faq.html', {'idioma': get_idioma(request)})


# ─── Crear CV independiente ───────────────────────────────────────────────────

@login_required
def crear_cv(request):
    profile = get_or_create_profile(request.user)
    cvs_usuario = CVUsuario.objects.filter(usuario=request.user)
    return render(request, 'ofertas/crear_cv.html', {
        'idioma': get_idioma(request),
        'cvs_usuario': cvs_usuario,
        'profile': profile,
        'contadores': get_contadores(request.user),
    })


@login_required
@require_POST
@rate_limit('mejorar_cv', limite=10, periodo=3600)
def mejorar_cv_ia(request):
    cv_texto = sanitizar_texto(request.POST.get('cv_texto', ''), max_length=50000).strip()
    if not cv_texto:
        return JsonResponse({'status': 'error', 'mensaje': 'CV vacío.'}, status=400)

    token = _get_groq_token(request)
    idioma = get_idioma(request)

    if idioma == 'en':
        prompt = f"""You are an expert CV writer. Restructure and improve this CV professionally.
Rules:
- Keep ALL real information, do not invent anything
- Improve wording and structure
- Use clear sections: Profile, Experience, Projects, Education, Skills, Languages
- Return ONLY the improved CV, no explanations

CV:
{sanitizar_prompt(cv_texto, max_length=20000)}"""
    else:
        prompt = f"""Eres un experto redactor de CVs. Restructura y mejora este CV de forma profesional.
Reglas:
- Mantén TODA la información real, no inventes nada
- Mejora la redacción y estructura
- Usa secciones claras: Perfil, Experiencia, Proyectos, Formación, Habilidades, Idiomas
- Devuelve SOLO el CV mejorado, sin explicaciones

CV:
{sanitizar_prompt(cv_texto, max_length=20000)}"""

    from .cv import _llamar_groq
    try:
        texto_mejorado = _llamar_groq(prompt, max_tokens=2000, token=token)
        html = render_md(texto_mejorado)
        return JsonResponse({'status': 'ok', 'texto': texto_mejorado, 'html': html})
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=500)


@login_required
def descargar_pdf_libre(request):
    if request.method != 'POST':
        return redirect('crear_cv')

    profile = get_or_create_profile(request.user)
    cv_contenido = sanitizar_texto(request.POST.get('cv_contenido', ''), max_length=50000).strip()
    if not cv_contenido:
        return redirect('crear_cv')

    plantilla = request.POST.get('plantilla', 'neutra')
    if plantilla not in ('neutra', 'profesional', 'moderna'):
        plantilla = 'neutra'

    nombre        = sanitizar_texto(request.POST.get('nombre', request.user.username), max_length=100)
    subtitulo     = sanitizar_texto(request.POST.get('subtitulo', ''), max_length=200)
    email         = sanitizar_texto(request.POST.get('email', ''), max_length=100)
    telefono      = sanitizar_texto(request.POST.get('telefono', ''), max_length=30)
    linkedin      = sanitizar_texto(request.POST.get('linkedin', ''), max_length=150)
    ubicacion_pdf = sanitizar_texto(request.POST.get('ubicacion', ''), max_length=100)
    opcion_foto   = request.POST.get('opcion_foto', 'ninguna')

    foto_path = None
    if opcion_foto == 'perfil' and profile.foto:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        tmp.write(bytes(profile.foto))
        tmp.close()
        foto_path = tmp.name

    from .pdf import generar_pdf as gen_pdf
    datos = {
        'nombre': nombre, 'subtitulo': subtitulo,
        'email': email, 'telefono': telefono,
        'linkedin': linkedin, 'ubicacion': ubicacion_pdf,
    }
    buffer = gen_pdf(datos, cv_contenido, plantilla=plantilla, foto_path=foto_path)

    if foto_path:
        try:
            os.unlink(foto_path)
        except Exception:
            pass

    nombre_archivo = f"CV_{nombre.replace(' ', '_')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response