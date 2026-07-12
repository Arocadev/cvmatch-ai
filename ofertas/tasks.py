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
        from .cv import _llamar_groq
        from .security import sanitizar_prompt
        import markdown as md

        if idioma == 'en':
            prompt = f"""You are an expert CV writer. Restructure and improve this CV professionally.
Rules: Keep ALL real information. Improve wording and structure.
Use clear sections: Profile, Experience, Projects, Education, Skills, Languages.
Return ONLY the improved CV, no explanations.

CV:
{sanitizar_prompt(cv_texto, max_length=20000)}"""
        else:
            prompt = f"""Eres un experto redactor de CVs. Restructura y mejora este CV de forma profesional.
Reglas: Mantén TODA la información real. Mejora la redacción y estructura.
Secciones: Perfil, Experiencia, Proyectos, Formación, Habilidades, Idiomas.
Devuelve SOLO el CV mejorado, sin explicaciones.

CV:
{sanitizar_prompt(cv_texto, max_length=20000)}"""

        texto = _llamar_groq(prompt, max_tokens=2000, token=token)
        html  = md.markdown(texto, extensions=['nl2br'])
        return {'status': 'ok', 'texto': texto, 'html': html}

    except Exception as exc:
        logger.error(f'task_mejorar_cv error: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def task_adaptar_cv(self, oferta_texto: str, cv_texto: str, idioma: str = 'es', token: str | None = None):
    try:
        from .cv import generar_cv_adaptado
        from .security import sanitizar_prompt
        import markdown as md

        texto = generar_cv_adaptado(
            sanitizar_prompt(oferta_texto, max_length=8000),
            sanitizar_prompt(cv_texto,     max_length=20000),
            idioma,
            token=token,
        )
        html = md.markdown(texto, extensions=['nl2br'])
        return {'status': 'ok', 'texto': texto, 'html': html}

    except Exception as exc:
        logger.error(f'task_adaptar_cv error: {exc}')
        raise self.retry(exc=exc)