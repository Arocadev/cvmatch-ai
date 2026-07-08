import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Image as RLImage

W, H = A4

# ─── Colores por plantilla ───────────────────────────────────────────────────
PALETAS = {
    'neutra':       {'primario': colors.HexColor('#374151'), 'acento': colors.HexColor('#6B7280'),  'fondo_cab': colors.HexColor('#F9FAFB')},
    'profesional':  {'primario': colors.HexColor('#1253A4'), 'acento': colors.HexColor('#0A3A78'),  'fondo_cab': colors.HexColor('#1253A4')},
    'moderna':      {'primario': colors.HexColor('#16a34a'), 'acento': colors.HexColor('#15803d'),  'fondo_cab': colors.HexColor('#16a34a')},
}

def _estilos_base(paleta):
    p = PALETAS[paleta]
    ss = getSampleStyleSheet()
    return {
        'nombre': ParagraphStyle('nombre', fontSize=20, fontName='Helvetica-Bold', textColor=p['primario'], spaceAfter=2, alignment=TA_LEFT),
        'subtitulo': ParagraphStyle('subtitulo', fontSize=11, fontName='Helvetica', textColor=p['acento'], spaceAfter=2),
        'contacto': ParagraphStyle('contacto', fontSize=8.5, fontName='Helvetica', textColor=colors.HexColor('#6B7280'), spaceAfter=1),
        'seccion': ParagraphStyle('seccion', fontSize=9, fontName='Helvetica-Bold', textColor=p['primario'], spaceBefore=14, spaceAfter=4, textTransform='uppercase', letterSpacing=1),
        'normal': ParagraphStyle('normal', fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#374151'), spaceAfter=3, leading=13),
        'negrita': ParagraphStyle('negrita', fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#0f172a'), spaceAfter=2),
        'pequeño': ParagraphStyle('pequeño', fontSize=8, fontName='Helvetica', textColor=colors.HexColor('#6B7280'), spaceAfter=2),
    }

def _linea(paleta):
    return HRFlowable(width='100%', thickness=1, color=PALETAS[paleta]['primario'], spaceAfter=6, spaceBefore=2)

def _foto(foto_path, size=2.5*cm):
    if foto_path and os.path.isfile(foto_path):
        try:
            img = RLImage(foto_path, width=size, height=size)
            img.hAlign = 'RIGHT'
            return img
        except Exception:
            pass
    return None

def _parsear_secciones(texto):
    """Divide el texto del CV en secciones por líneas --- o ### SECCION"""
    import re
    secciones = []
    seccion_actual = {'titulo': None, 'contenido': []}

    for linea in texto.split('\n'):
        linea = linea.strip()
        if not linea or linea == '---':
            continue
        # Detecta títulos de sección: ### TITULO o TITULO en mayúsculas solo
        if re.match(r'^#{1,3}\s+', linea):
            if seccion_actual['contenido'] or seccion_actual['titulo']:
                secciones.append(seccion_actual)
            titulo = re.sub(r'^#{1,3}\s+', '', linea).strip()
            seccion_actual = {'titulo': titulo, 'contenido': []}
        elif linea.isupper() and len(linea) > 3 and len(linea) < 50:
            if seccion_actual['contenido'] or seccion_actual['titulo']:
                secciones.append(seccion_actual)
            seccion_actual = {'titulo': linea, 'contenido': []}
        else:
            # Limpia markdown básico
            linea = re.sub(r'\*\*(.*?)\*\*', r'\1', linea)
            linea = re.sub(r'\*(.*?)\*', r'\1', linea)
            linea = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', linea)
            seccion_actual['contenido'].append(linea)

    if seccion_actual['contenido'] or seccion_actual['titulo']:
        secciones.append(seccion_actual)

    return secciones

def _cabecera_neutra(datos, estilos, foto_path, story):
    foto = _foto(foto_path)
    nombre_p = Paragraph(datos.get('nombre', ''), estilos['nombre'])
    subtitulo_p = Paragraph(datos.get('subtitulo', ''), estilos['subtitulo'])
    contacto_p = Paragraph(datos.get('contacto', ''), estilos['contacto'])

    if foto:
        tabla = Table([[nombre_p, foto]], colWidths=[13*cm, 3*cm])
        tabla.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
        story.append(tabla)
    else:
        story.append(nombre_p)

    story.append(subtitulo_p)
    story.append(contacto_p)
    story.append(Spacer(1, 6))
    story.append(_linea('neutra'))

def _cabecera_profesional(datos, estilos, foto_path, story):
    from reportlab.platypus import Table, TableStyle
    p = PALETAS['profesional']
    nombre_style = ParagraphStyle('n', fontSize=22, fontName='Helvetica-Bold', textColor=colors.white, spaceAfter=2)
    sub_style = ParagraphStyle('s', fontSize=11, fontName='Helvetica', textColor=colors.HexColor('#C7DEFF'), spaceAfter=2)
    cont_style = ParagraphStyle('c', fontSize=8.5, fontName='Helvetica', textColor=colors.HexColor('#93C5FD'), spaceAfter=1)

    nombre_p = Paragraph(datos.get('nombre', ''), nombre_style)
    subtitulo_p = Paragraph(datos.get('subtitulo', ''), sub_style)
    contacto_p = Paragraph(datos.get('contacto', ''), cont_style)

    foto = _foto(foto_path)
    contenido_izq = [nombre_p, subtitulo_p, contacto_p]

    if foto:
        foto_blanca = _foto(foto_path, size=2.8*cm)
        tabla = Table([[contenido_izq, foto_blanca]], colWidths=[13*cm, 3*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), p['fondo_cab']),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('TOPPADDING', (0,0), (-1,-1), 14),
            ('BOTTOMPADDING', (0,0), (-1,-1), 14),
            ('LEFTPADDING', (0,0), (0,-1), 16),
            ('RIGHTPADDING', (-1,0), (-1,-1), 16),
        ]))
    else:
        tabla = Table([[contenido_izq]], colWidths=[16*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), p['fondo_cab']),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 14),
            ('BOTTOMPADDING', (0,0), (-1,-1), 14),
            ('LEFTPADDING', (0,0), (0,-1), 16),
        ]))

    story.append(tabla)
    story.append(Spacer(1, 12))

def _cabecera_moderna(datos, estilos, foto_path, story):
    p = PALETAS['moderna']
    nombre_style = ParagraphStyle('n', fontSize=20, fontName='Helvetica-Bold', textColor=colors.white)
    sub_style = ParagraphStyle('s', fontSize=10, fontName='Helvetica', textColor=colors.HexColor('#D1FAE5'))
    cont_style = ParagraphStyle('c', fontSize=8.5, fontName='Helvetica', textColor=colors.HexColor('#A7F3D0'))

    nombre_p = Paragraph(datos.get('nombre', ''), nombre_style)
    subtitulo_p = Paragraph(datos.get('subtitulo', ''), sub_style)
    contacto_p = Paragraph(datos.get('contacto', ''), cont_style)

    foto = _foto(foto_path)

    if foto:
        tabla = Table([[nombre_p, foto]], colWidths=[13*cm, 3*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), p['fondo_cab']),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('TOPPADDING', (0,0), (-1,-1), 16),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (0,-1), 16),
            ('RIGHTPADDING', (-1,0), (-1,-1), 16),
        ]))
        story.append(tabla)
        sub_tabla = Table([[subtitulo_p], [contacto_p]], colWidths=[16*cm])
        sub_tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), p['fondo_cab']),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 14),
            ('LEFTPADDING', (0,0), (-1,-1), 16),
        ]))
        story.append(sub_tabla)
    else:
        tabla = Table([[nombre_p], [subtitulo_p], [contacto_p]], colWidths=[16*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), p['fondo_cab']),
            ('TOPPADDING', (0,0), (0,0), 16),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 14),
            ('LEFTPADDING', (0,0), (-1,-1), 16),
        ]))
        story.append(tabla)

    story.append(Spacer(1, 12))

def generar_pdf(datos, cv_texto, plantilla='profesional', foto_path=None):
    """
    datos = {
        'nombre': str,
        'subtitulo': str,
        'contacto': str,
    }
    cv_texto = texto plano del CV adaptado
    plantilla = 'neutra' | 'profesional' | 'moderna'
    foto_path = ruta al archivo de imagen o None
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8*cm,
        rightMargin=1.8*cm,
        topMargin=1.5*cm,
        bottomMargin=1.8*cm,
    )

    estilos = _estilos_base(plantilla)
    story = []

    # Cabecera según plantilla
    if plantilla == 'neutra':
        _cabecera_neutra(datos, estilos, foto_path, story)
    elif plantilla == 'profesional':
        _cabecera_profesional(datos, estilos, foto_path, story)
    elif plantilla == 'moderna':
        _cabecera_moderna(datos, estilos, foto_path, story)

    # Cuerpo — parsea secciones del CV
    secciones = _parsear_secciones(cv_texto)

    for seccion in secciones:
        if seccion['titulo']:
            story.append(Paragraph(seccion['titulo'], estilos['seccion']))
            story.append(_linea(plantilla))

        for linea in seccion['contenido']:
            if not linea.strip():
                story.append(Spacer(1, 4))
                continue
            if linea.startswith('- ') or linea.startswith('• '):
                texto = '• ' + linea[2:]
                story.append(Paragraph(texto, estilos['normal']))
            else:
                story.append(Paragraph(linea, estilos['normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer