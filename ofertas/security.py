import logging
import re
from functools import wraps
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger('seguridad')

PDF_MAGIC_BYTES = b'%PDF'
IMAGEN_MAGIC_BYTES = [
    b'\xff\xd8\xff',        # JPEG
    b'\x89PNG\r\n\x1a\n',  # PNG
    b'GIF87a',              # GIF
    b'GIF89a',              # GIF
    b'RIFF',                # WebP
]

# ─── Rate limiting ────────────────────────────────────────────────────────────

def rate_limit(key_prefix, limite, periodo):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Desactivado en desarrollo
            if getattr(settings, 'DEBUG', False):
                return view_func(request, *args, **kwargs)

            ip = get_client_ip(request)
            cache_key = f'rl:{key_prefix}:{ip}'
            intentos = cache.get(cache_key, 0)
            if intentos >= limite:
                idioma = request.session.get('idioma', 'es')
                logger.warning(f'Rate limit alcanzado — {key_prefix} — IP: {ip}')
                mensaje = 'Demasiados intentos. Espera unos minutos.' if idioma == 'es' else 'Too many attempts. Please wait.'
                return HttpResponse(mensaje, status=429, content_type='text/plain; charset=utf-8')
            cache.set(cache_key, intentos + 1, periodo)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


# ─── Validación de archivos ───────────────────────────────────────────────────

def validar_pdf(archivo):
    if not archivo:
        return False, 'No se ha proporcionado ningún archivo.'
    max_size = getattr(settings, 'MAX_PDF_SIZE_BYTES', 5 * 1024 * 1024)
    if archivo.size > max_size:
        return False, 'El archivo supera el límite de 5 MB.'
    if not archivo.name.lower().endswith('.pdf'):
        return False, 'Solo se permiten archivos PDF.'
    primeros_bytes = archivo.read(4)
    archivo.seek(0)
    if primeros_bytes != PDF_MAGIC_BYTES:
        logger.warning(f'Intento de subida de archivo no PDF — Nombre: {archivo.name}')
        return False, 'El archivo no es un PDF válido.'
    return True, None


def validar_imagen(archivo):
    if not archivo:
        return False, 'No se ha proporcionado ningún archivo.'
    max_size = getattr(settings, 'MAX_FOTO_SIZE_BYTES', 2 * 1024 * 1024)
    if archivo.size > max_size:
        return False, 'La imagen no puede superar 2 MB.'
    nombre = archivo.name.lower()
    if not any(nombre.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        return False, 'Solo se permiten imágenes JPG, PNG, GIF o WebP.'
    primeros_bytes = archivo.read(8)
    archivo.seek(0)
    es_imagen = any(primeros_bytes.startswith(magic) for magic in IMAGEN_MAGIC_BYTES)
    if not es_imagen:
        logger.warning(f'Intento de subida de archivo no imagen — Nombre: {archivo.name}')
        return False, 'El archivo no es una imagen válida.'
    return True, None


# ─── Sanitización ─────────────────────────────────────────────────────────────

def sanitizar_texto(texto, max_length=50000):
    if not texto:
        return ''
    texto = texto.replace('\x00', '')
    return texto[:max_length].strip()


def sanitizar_busqueda(texto, max_length=200):
    if not texto:
        return ''
    texto = texto.replace('\x00', '')
    permitidos = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,+-/áéíóúüñÁÉÍÓÚÜÑàèìòùÀÈÌÒÙ#@_')
    texto = ''.join(c for c in texto if c in permitidos)
    return texto[:max_length].strip()


def sanitizar_prompt(texto, max_length=30000):
    """
    Sanitiza texto antes de mandarlo a Groq.
    Elimina intentos de prompt injection.
    """
    if not texto:
        return ''
    texto = texto.replace('\x00', '')
    patrones_peligrosos = [
        r'ignore previous instructions',
        r'ignore all previous',
        r'disregard.*instructions',
        r'you are now',
        r'act as',
        r'new instructions:',
        r'system:',
        r'\[system\]',
        r'<\|im_start\|>',
        r'<\|im_end\|>',
    ]
    texto_lower = texto.lower()
    for patron in patrones_peligrosos:
        if re.search(patron, texto_lower):
            logger.warning(f'Posible prompt injection detectado — patrón: {patron}')
            break
    return texto[:max_length].strip()