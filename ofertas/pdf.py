import io
import re
import base64
import mimetypes
from django.template.loader import render_to_string
from weasyprint import HTML, CSS


def _foto_base64(foto_path):
    """Convierte foto a data URI base64."""
    if not foto_path:
        return None
    try:
        mime = mimetypes.guess_type(foto_path)[0] or 'image/jpeg'
        with open(foto_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'data:{mime};base64,{b64}'
    except Exception:
        return None


def generar_pdf(datos_personales: dict, cv_contenido, plantilla: str = 'profesional', foto_path: str = None) -> bytes:
    """
    Genera un PDF a partir de datos personales y cv_contenido.
    cv_contenido puede ser:
      - dict (JSON estructurado de la IA) — flujo principal
      - str (texto plano) — flujo de compatibilidad
    """
    # Si es texto plano, convertir a estructura mínima
    if isinstance(cv_contenido, str):
        try:
            import json
            cv_contenido = json.loads(cv_contenido)
        except Exception:
            cv_contenido = _texto_a_estructura(cv_contenido, datos_personales)

    # Foto como base64
    foto_data_uri = _foto_base64(foto_path)

    # Fusionar datos del formulario con los del JSON
    # Los datos del formulario tienen prioridad sobre los del JSON
    nombre    = datos_personales.get('nombre') or cv_contenido.get('name', '')
    subtitulo = datos_personales.get('subtitulo') or cv_contenido.get('title', '')
    email     = datos_personales.get('email') or cv_contenido.get('contact', {}).get('email', '')
    telefono  = datos_personales.get('telefono') or cv_contenido.get('contact', {}).get('phone', '')
    linkedin  = datos_personales.get('linkedin') or cv_contenido.get('contact', {}).get('linkedin', '')
    ubicacion = datos_personales.get('ubicacion') or cv_contenido.get('contact', {}).get('location', '')
    github    = cv_contenido.get('contact', {}).get('github', '')

    profile  = cv_contenido.get('profile', '')
    sections = cv_contenido.get('sections', [])

    contacto = []
    if ubicacion: contacto.append(ubicacion)
    if telefono:  contacto.append(telefono)
    if email:     contacto.append(email)
    if linkedin:  contacto.append(linkedin)
    if github:    contacto.append(github)

    ctx = {
        'nombre':    nombre,
        'subtitulo': subtitulo,
        'contacto':  contacto,
        'profile':   profile,
        'sections':  sections,
        'foto':      foto_data_uri,
    }

    if plantilla not in ('ats', 'executive', 'sidebar', 'minimal', 'compact'):
        plantilla = 'executive'

    html_str = render_to_string(f'pdf/{plantilla}.html', ctx)
    css_path = f'ofertas/static/pdf/{plantilla}.css'

    try:
        with open(css_path, 'r') as f:
            css_str = f.read()
        css = CSS(string=css_str)
    except FileNotFoundError:
        css = CSS(string=_css_base())

    buffer = io.BytesIO()
    HTML(string=html_str).write_pdf(buffer, stylesheets=[css])
    return buffer.getvalue()


def _texto_a_estructura(texto, datos_personales=None):
    """Convierte texto plano a estructura JSON mínima."""
    return {
        'name':    datos_personales.get('nombre', '') if datos_personales else '',
        'title':   datos_personales.get('subtitulo', '') if datos_personales else '',
        'profile': '',
        'contact': {
            'email':    datos_personales.get('email', '') if datos_personales else '',
            'phone':    datos_personales.get('telefono', '') if datos_personales else '',
            'location': datos_personales.get('ubicacion', '') if datos_personales else '',
            'linkedin': datos_personales.get('linkedin', '') if datos_personales else '',
            'github':   '',
        },
        'sections': [
            {
                'title': 'CONTENIDO',
                'type':  'text',
                'items': [texto],
            }
        ]
    }


def _css_base():
    return """
    @page { size: A4; margin: 0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; font-size: 10pt; color: #111; }
    """