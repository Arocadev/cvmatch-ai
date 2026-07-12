import io
import re
from weasyprint import HTML, CSS


def sanitizar_para_pdf(texto: str) -> str:
    """Sustituye caracteres problemáticos para WeasyPrint."""
    reemplazos = {
        '\u2019': "'",   # comilla derecha
        '\u2018': "'",   # comilla izquierda
        '\u201c': '"',   # comilla doble izquierda
        '\u201d': '"',   # comilla doble derecha
        '\u2013': '-',   # guión corto
        '\u2014': '-',   # guión largo
        '\u2022': '•',   # bullet (este sí funciona)
        '\u00b7': '•',   # punto medio
        '\u2026': '...',  # puntos suspensivos
        '\u00a0': ' ',   # espacio no separable
        '\ufb01': 'fi',  # ligadura fi
        '\ufb02': 'fl',  # ligadura fl
    }
    for char, reemplazo in reemplazos.items():
        texto = texto.replace(char, reemplazo)
    # Eliminar cualquier carácter de control o no imprimible que no sea salto de línea/tab
    texto = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\x80-\xFF\u00C0-\u024F\u0400-\u04FF•·→←↑↓]', '', texto)
    return texto


def texto_a_html(texto: str) -> str:
    """Convierte texto plano con markdown básico a HTML para el PDF."""
    lines = texto.split('\n')
    html_lines = []
    for line in lines:
        line = line.rstrip()
        if not line:
            html_lines.append('<br>')
            continue
        # Separadores ---
        if line.strip() in ('---', '***', '___'):
            html_lines.append('<hr>')
            continue
        # Ignorar líneas de tabla markdown (|----|)
        if re.match(r'^\|[-| :]+\|$', line.strip()):
            continue
        # Convertir filas de tabla a párrafo simple
        if line.strip().startswith('|') and line.strip().endswith('|'):
            celdas = [c.strip() for c in line.strip()[1:-1].split('|')]
            line = ' | '.join(c for c in celdas if c)
        # Eliminar links markdown [texto](url) -> texto
        line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'', line)
        # Encabezados markdown
        if line.startswith('### '):
            html_lines.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('# '):
            html_lines.append(f'<h1>{line[2:]}</h1>')
        # Negrita **texto**
        elif line.startswith('**') and line.endswith('**') and len(line) > 4:
            html_lines.append(f'<p><strong>{line[2:-2]}</strong></p>')
        # Listas
        elif line.startswith('- ') or line.startswith('• '):
            html_lines.append(f'<li>{line[2:]}</li>')
        elif line.startswith('* '):
            html_lines.append(f'<li>{line[2:]}</li>')
        else:
            # Inline bold
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            html_lines.append(f'<p>{line}</p>')

    # Agrupar <li> en <ul>
    result = []
    in_list = False
    for h in html_lines:
        if h.startswith('<li>'):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(h)
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(h)
    if in_list:
        result.append('</ul>')
    return '\n'.join(result)


def generar_pdf(datos: dict, cv_texto: str, plantilla: str = 'profesional', foto_path: str = None) -> bytes:
    cv_texto = sanitizar_para_pdf(cv_texto)
    cv_html  = texto_a_html(cv_texto)

    nombre    = datos.get('nombre', '')
    subtitulo = datos.get('subtitulo', '')
    email     = datos.get('email', '')
    telefono  = datos.get('telefono', '')
    linkedin  = datos.get('linkedin', '')
    ubicacion = datos.get('ubicacion', '')

    # Contacto
    contacto_items = []
    if ubicacion: contacto_items.append(ubicacion)
    if telefono:  contacto_items.append(telefono)
    if email:     contacto_items.append(email)
    if linkedin:  contacto_items.append(linkedin)
    contacto_html = ' &bull; '.join(contacto_items)

    # Foto
    foto_html = ''
    if foto_path:
        foto_html = f'<img src="{foto_path}" class="foto-perfil">'

    # Colores por plantilla
    if plantilla == 'profesional':
        color_primario  = '#1253A4'
        color_cabecera  = '#1253A4'
        texto_cabecera  = '#ffffff'
        color_seccion   = '#1253A4'
        borde_seccion   = '#1253A4'
    elif plantilla == 'moderna':
        color_primario  = '#16a34a'
        color_cabecera  = '#16a34a'
        texto_cabecera  = '#ffffff'
        color_seccion   = '#16a34a'
        borde_seccion   = '#16a34a'
    else:  # neutra
        color_primario  = '#374151'
        color_cabecera  = '#f9fafb'
        texto_cabecera  = '#0f172a'
        color_seccion   = '#374151'
        borde_seccion   = '#9ca3af'

    css = f"""
    @page {{
        size: A4;
        margin: 0;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 10pt;
        color: #111;
        background: #fff;
    }}
    .cabecera {{
        background: {color_cabecera};
        color: {texto_cabecera};
        padding: 28px 36px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        min-height: 110px;
    }}
    .cabecera-texto h1 {{
        font-size: 22pt;
        font-weight: bold;
        margin-bottom: 4px;
        color: {texto_cabecera};
    }}
    .cabecera-texto .subtitulo {{
        font-size: 10pt;
        opacity: 0.85;
        margin-bottom: 8px;
    }}
    .cabecera-texto .contacto {{
        font-size: 8.5pt;
        opacity: 0.8;
    }}
    .foto-perfil {{
        width: 80px;
        height: 80px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid rgba(255,255,255,0.4);
        flex-shrink: 0;
    }}
    .contenido {{
        padding: 24px 36px;
    }}
    h1, h2 {{
        font-size: 10pt;
        font-weight: bold;
        color: {color_seccion};
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 18px;
        margin-bottom: 6px;
        padding-bottom: 4px;
        border-bottom: 1.5px solid {borde_seccion};
    }}
    h3 {{
        font-size: 10pt;
        font-weight: bold;
        color: #111;
        margin-top: 10px;
        margin-bottom: 3px;
    }}
    p {{
        margin-bottom: 4px;
        line-height: 1.5;
        font-size: 9.5pt;
    }}
    ul {{
        padding-left: 16px;
        margin-bottom: 6px;
    }}
    li {{
        margin-bottom: 3px;
        font-size: 9.5pt;
        line-height: 1.4;
    }}
    strong {{ font-weight: bold; }}
    hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 8px 0; }}
    br {{ display: block; margin-bottom: 4px; }}
    """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body>
        <div class="cabecera">
            <div class="cabecera-texto">
                <h1 style="color:{texto_cabecera}; border:none; text-transform:none; letter-spacing:0; margin:0 0 4px 0; padding:0;">{nombre}</h1>
                {'<p class="subtitulo">' + subtitulo + '</p>' if subtitulo else ''}
                {'<p class="contacto">' + contacto_html + '</p>' if contacto_html else ''}
            </div>
            {foto_html}
        </div>
        <div class="contenido">
            {cv_html}
        </div>
    </body>
    </html>
    """

    buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(
        buffer,
        stylesheets=[CSS(string=css)]
    )
    return buffer.getvalue()