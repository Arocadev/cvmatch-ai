"""
Archivo: ofertas/tasks.py
Tareas Celery para llamadas a Groq en background.
"""
from celery import shared_task
import logging

logger = logging.getLogger('seguridad')


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def task_resumir_oferta(self, oferta_id: int, idioma: str = 'es', token: str | None = None):
    try:
        from .models import Oferta
        from .cv import resumir_oferta
        from .security import sanitizar_prompt
        import markdown as md

        oferta = Oferta.objects.get(pk=oferta_id)
        if oferta.resumen_ia:
            return {'status': 'cached', 'oferta_id': oferta_id}

        resumen_raw = resumir_oferta(
            sanitizar_prompt(oferta.descripcion, max_length=8000),
            idioma,
            token=token,
        )
        oferta.resumen_ia = md.markdown(resumen_raw, extensions=['nl2br'])
        oferta.save(update_fields=['resumen_ia'])
        return {'status': 'ok', 'oferta_id': oferta_id, 'html': oferta.resumen_ia}

    except Oferta.DoesNotExist:
        return {'status': 'not_found', 'oferta_id': oferta_id}
    except Exception as exc:
        logger.error(f'task_resumir_oferta error oferta={oferta_id}: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def task_analizar_cv(self, oferta_id: int, cv_texto: str, idioma: str = 'es', token: str | None = None):
    try:
        from .models import Oferta
        from .cv import analizar_oferta_para_cv
        from .security import sanitizar_prompt
        import markdown as md

        oferta = Oferta.objects.get(pk=oferta_id)
        analisis_raw = analizar_oferta_para_cv(
            sanitizar_prompt(oferta.descripcion, max_length=8000),
            sanitizar_prompt(cv_texto, max_length=20000),
            idioma,
            token=token,
        )
        return {'status': 'ok', 'html': md.markdown(analisis_raw, extensions=['nl2br'])}

    except Oferta.DoesNotExist:
        return {'status': 'not_found'}
    except Exception as exc:
        logger.error(f'task_analizar_cv error oferta={oferta_id}: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def task_generar_cv(self, oferta_id: int, cv_texto: str, idioma: str = 'es', token: str | None = None):
    try:
        from .models import Oferta
        from .cv import generar_cv_adaptado
        from .security import sanitizar_prompt
        import markdown as md

        oferta = Oferta.objects.get(pk=oferta_id)
        cv_raw = generar_cv_adaptado(
            sanitizar_prompt(oferta.descripcion, max_length=8000),
            sanitizar_prompt(cv_texto, max_length=20000),
            idioma,
            token=token,
        )
        return {
            'status': 'ok',
            'raw': cv_raw,
            'html': md.markdown(cv_raw, extensions=['nl2br'])
        }

    except Oferta.DoesNotExist:
        return {'status': 'not_found'}
    except Exception as exc:
        logger.error(f'task_generar_cv error oferta={oferta_id}: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def task_mejorar_cv(self, cv_texto: str, idioma: str = 'es', token: str | None = None):
    try:
        import json
        from .cv import mejorar_cv_json
        from .security import sanitizar_prompt

        datos = mejorar_cv_json(
            sanitizar_prompt(cv_texto, max_length=20000),
            idioma,
            token=token,
        )
        texto = json.dumps(datos, ensure_ascii=False, indent=2)
        # Para el preview en el navegador, generamos HTML legible
        html = _json_a_html_preview(datos)
        return {'status': 'ok', 'texto': texto, 'html': html, 'json': datos}

    except Exception as exc:
        logger.error(f'task_mejorar_cv error: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def task_adaptar_cv(self, oferta_texto: str, cv_texto: str, idioma: str = 'es', token: str | None = None):
    try:
        import json
        from .cv import generar_cv_json
        from .security import sanitizar_prompt

        datos = generar_cv_json(
            sanitizar_prompt(oferta_texto, max_length=8000),
            sanitizar_prompt(cv_texto,     max_length=20000),
            idioma,
            token=token,
        )
        texto = json.dumps(datos, ensure_ascii=False, indent=2)
        html = _json_a_html_preview(datos)
        return {'status': 'ok', 'texto': texto, 'html': html, 'json': datos}

    except Exception as exc:
        logger.error(f'task_adaptar_cv error: {exc}')
        raise self.retry(exc=exc)


def _json_a_html_preview(datos: dict) -> str:
    """Convierte JSON de CV a HTML legible para la vista previa del navegador."""
    html = []
    nombre = datos.get('name', '')
    titulo = datos.get('title', '')
    profile = datos.get('profile', '')

    if nombre:
        html.append(f'<h2 style="font-size:16px;font-weight:800;color:#0f172a;margin-bottom:2px;">{nombre}</h2>')
    if titulo:
        html.append(f'<p style="font-size:13px;color:#1253A4;font-weight:600;margin-bottom:8px;">{titulo}</p>')
    if profile:
        html.append(f'<p style="font-size:13px;color:#374151;line-height:1.7;margin-bottom:12px;">{profile}</p>')

    for seccion in datos.get('sections', []):
        html.append(f'<h3 style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#1253A4;border-bottom:1px solid #e2e8f0;padding-bottom:3px;margin:12px 0 8px;">{seccion.get("title","")}</h3>')

        tipo = seccion.get('type', '')
        items = seccion.get('items', [])

        if tipo == 'timeline':
            for item in items:
                t = item.get('title', '')
                s = item.get('subtitle', '')
                d = item.get('date', '')
                bullets = item.get('bullets', [])
                html.append(f'<div style="margin-bottom:8px;">')
                html.append(f'<div style="display:flex;justify-content:space-between;"><strong style="font-size:12px;">{t}</strong><span style="font-size:11px;color:#64748b;">{d}</span></div>')
                if s: html.append(f'<p style="font-size:11px;color:#475569;font-style:italic;margin:1px 0 4px;">{s}</p>')
                if bullets:
                    html.append('<ul style="padding-left:14px;margin-top:2px;">')
                    for b in bullets:
                        html.append(f'<li style="font-size:12px;color:#374151;margin-bottom:2px;">{b}</li>')
                    html.append('</ul>')
                html.append('</div>')

        elif tipo == 'chips':
            html.append('<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:2px;">')
            for item in items:
                html.append(f'<span style="background:#EBF3FF;color:#1253A4;border:1px solid #C7DEFF;border-radius:4px;padding:3px 9px;font-size:11px;font-weight:600;">{item}</span>')
            html.append('</div>')

        elif tipo == 'list':
            html.append('<ul style="padding-left:14px;">')
            for item in items:
                html.append(f'<li style="font-size:12px;color:#374151;margin-bottom:2px;">{item}</li>')
            html.append('</ul>')

    return ''.join(html)