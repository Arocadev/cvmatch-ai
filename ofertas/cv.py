import os
import re
import time
import json
import fitz
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODELO = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')


def _get_cliente(token=None):
    api_key = token or os.getenv('GROQ_API_KEY')
    return Groq(api_key=api_key)


def limpiar_respuesta(texto):
    texto = re.sub(r'<think>[\s\S]*?</think>', '', texto)
    texto = re.sub(r'<think>[\s\S]*', '', texto)
    return texto.strip()


def extraer_texto_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texto = ''
    for page in doc:
        texto += page.get_text()
    return texto


def _llamar_groq(prompt, max_tokens=500, token=None):
    cliente = _get_cliente(token)
    for intento in range(3):
        try:
            respuesta = cliente.chat.completions.create(
                model=MODELO,
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=max_tokens,
            )
            return limpiar_respuesta(respuesta.choices[0].message.content)
        except Exception as e:
            error_str = str(e).lower()
            if 'rate_limit' in error_str or '429' in error_str:
                if intento < 2:
                    time.sleep((intento + 1) * 5)
                    continue
                raise Exception('El servicio de IA está temporalmente saturado. Espera unos segundos.')
            raise


def resumir_oferta(descripcion_oferta, idioma='es', token=None):
    if idioma == 'en':
        prompt = f"""Analyze this job offer and extract the key information in this exact format:

POSITION: (job title)
COMPANY: (company name if available)
MODALITY: (Remote / Hybrid / On-site / Not specified)
EXPERIENCE: (years required or Not specified)
SALARY: (range if available or Not specified)
STACK: (main technologies and tools, separated by commas)
SUMMARY: (2-3 sentences explaining what the role is about)

Job offer:
{descripcion_oferta}

Respond ONLY with the format above."""
    else:
        prompt = f"""Analiza esta oferta de trabajo y extrae la información clave en este formato exacto:

PUESTO: (título del puesto)
EMPRESA: (nombre de la empresa si aparece)
MODALIDAD: (Remoto / Híbrido / Presencial / No especificado)
EXPERIENCIA: (años requeridos o No especificado)
SALARIO: (rango si aparece o No especificado)
STACK: (tecnologías y herramientas principales, separadas por comas)
RESUMEN: (2-3 frases explicando de qué trata el puesto)

Oferta:
{descripcion_oferta}

Responde SOLO con el formato indicado."""

    return _llamar_groq(prompt, max_tokens=800, token=token)


def analizar_oferta_para_cv(descripcion_oferta, cv_texto, idioma='es', token=None):
    if idioma == 'en':
        prompt = f"""You are an expert in ATS CV optimization.

Job offer:
{descripcion_oferta}

My CV:
{cv_texto}

Respond in this exact format:

COMPATIBILITY: X%
OFFER LEVEL: (Junior/Mid/Senior)

SUMMARY:
(2-3 sentences)

MISSING KEYWORDS:
(relevant ones only)

WHAT TO HIGHLIGHT:
(most relevant experiences)

CONCRETE CHANGES:
(specific and realistic)"""
    else:
        prompt = f"""Eres un experto en optimización de CVs para ATS.

Oferta de trabajo:
{descripcion_oferta}

Mi CV:
{cv_texto}

Responde en este formato exacto:

COMPATIBILIDAD: X%
NIVEL DE LA OFERTA: (Junior/Mid/Senior)

RESUMEN:
(2-3 frases)

PALABRAS CLAVE QUE FALTAN:
(solo las relevantes)

QUÉ DESTACAR:
(experiencias más relevantes)

CAMBIOS CONCRETOS:
(cambios específicos y realistas)"""

    return _llamar_groq(prompt, max_tokens=1000, token=token)


def generar_cv_json(descripcion_oferta, cv_texto, idioma='es', token=None):
    """
    Genera un CV adaptado en formato JSON estructurado.
    Devuelve un dict con las secciones del CV.
    """
    if idioma == 'en':
        prompt = f"""You are an expert CV writer specialized in ATS optimization.

Job offer:
{descripcion_oferta}

Candidate CV:
{cv_texto}

Rewrite the CV adapted to this offer and return ONLY a valid JSON object with this exact structure:
{{
  "name": "Full name",
  "title": "Professional title adapted to the offer",
  "profile": "Professional summary paragraph (3-4 sentences, adapted to the offer)",
  "contact": {{
    "email": "email if available",
    "phone": "phone if available",
    "location": "city, country",
    "linkedin": "linkedin URL if available",
    "github": "github URL if available"
  }},
  "sections": [
    {{
      "title": "EXPERIENCE",
      "type": "timeline",
      "items": [
        {{
          "title": "Job position",
          "subtitle": "Company name",
          "date": "Start date - End date",
          "bullets": ["achievement 1", "achievement 2"]
        }}
      ]
    }},
    {{
      "title": "PROJECTS",
      "type": "timeline",
      "items": [
        {{
          "title": "Project name",
          "subtitle": "Technologies used",
          "date": "Year or date range",
          "bullets": ["description 1", "description 2"]
        }}
      ]
    }},
    {{
      "title": "EDUCATION",
      "type": "timeline",
      "items": [
        {{
          "title": "Degree or course",
          "subtitle": "Institution",
          "date": "Year",
          "bullets": []
        }}
      ]
    }},
    {{
      "title": "SKILLS",
      "type": "chips",
      "items": ["skill1", "skill2", "skill3"]
    }},
    {{
      "title": "LANGUAGES",
      "type": "list",
      "items": ["Language — Level"]
    }}
  ]
}}

Rules:
- Keep ALL real information, do not invent anything
- Order sections by relevance to the offer
- Prioritize keywords from the offer
- Return ONLY the JSON, no explanations, no markdown, no ```json```

Job offer:
{descripcion_oferta}

Candidate CV:
{cv_texto}"""
    else:
        prompt = f"""Eres un experto en redacción de CVs optimizados para ATS.

Reescribe el CV adaptado a la oferta y devuelve SOLO un objeto JSON válido con esta estructura exacta:
{{
  "name": "Nombre completo",
  "title": "Título profesional adaptado a la oferta",
  "profile": "Párrafo de perfil profesional (3-4 frases, adaptado a la oferta)",
  "contact": {{
    "email": "email si está disponible",
    "phone": "teléfono si está disponible",
    "location": "ciudad, país",
    "linkedin": "URL de linkedin si está disponible",
    "github": "URL de github si está disponible"
  }},
  "sections": [
    {{
      "title": "EXPERIENCIA",
      "type": "timeline",
      "items": [
        {{
          "title": "Puesto de trabajo",
          "subtitle": "Nombre de la empresa",
          "date": "Fecha inicio - Fecha fin",
          "bullets": ["logro 1", "logro 2"]
        }}
      ]
    }},
    {{
      "title": "PROYECTOS",
      "type": "timeline",
      "items": [
        {{
          "title": "Nombre del proyecto",
          "subtitle": "Tecnologías usadas",
          "date": "Año o rango de fechas",
          "bullets": ["descripción 1", "descripción 2"]
        }}
      ]
    }},
    {{
      "title": "FORMACIÓN",
      "type": "timeline",
      "items": [
        {{
          "title": "Titulación o curso",
          "subtitle": "Centro educativo",
          "date": "Año",
          "bullets": []
        }}
      ]
    }},
    {{
      "title": "HABILIDADES",
      "type": "chips",
      "items": ["habilidad1", "habilidad2", "habilidad3"]
    }},
    {{
      "title": "IDIOMAS",
      "type": "list",
      "items": ["Idioma — Nivel"]
    }}
  ]
}}

Reglas:
- Mantén TODA la información real, no inventes nada
- Ordena las secciones por relevancia para la oferta
- Prioriza las palabras clave de la oferta
- Devuelve SOLO el JSON, sin explicaciones, sin markdown, sin ```json```

Oferta:
{descripcion_oferta}

CV del candidato:
{cv_texto}"""

    texto = _llamar_groq(prompt, max_tokens=3000, token=token)

    # Limpiar posibles bloques markdown
    texto = re.sub(r'```json\s*', '', texto)
    texto = re.sub(r'```\s*', '', texto)
    texto = texto.strip()

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        # Intentar extraer JSON del texto
        match = re.search(r'\{[\s\S]+\}', texto)
        if match:
            return json.loads(match.group())
        raise Exception('La IA no devolvió un JSON válido. Inténtalo de nuevo.')


def generar_cv_adaptado(descripcion_oferta, cv_texto, idioma='es', token=None):
    """Compatibilidad con el flujo anterior — devuelve texto."""
    datos = generar_cv_json(descripcion_oferta, cv_texto, idioma, token)
    return json.dumps(datos, ensure_ascii=False, indent=2)


def mejorar_cv_json(cv_texto, idioma='es', token=None):
    """Mejora un CV sin oferta y lo devuelve como JSON estructurado."""
    if idioma == 'en':
        prompt = f"""You are an expert CV writer. Restructure and improve this CV professionally.
Return ONLY a valid JSON object with this exact structure:
{{
  "name": "Full name",
  "title": "Professional title",
  "profile": "Professional summary (3-4 sentences)",
  "contact": {{
    "email": "", "phone": "", "location": "", "linkedin": "", "github": ""
  }},
  "sections": [
    {{"title": "EXPERIENCE", "type": "timeline", "items": [{{"title": "", "subtitle": "", "date": "", "bullets": []}}]}},
    {{"title": "PROJECTS", "type": "timeline", "items": [{{"title": "", "subtitle": "", "date": "", "bullets": []}}]}},
    {{"title": "EDUCATION", "type": "timeline", "items": [{{"title": "", "subtitle": "", "date": "", "bullets": []}}]}},
    {{"title": "SKILLS", "type": "chips", "items": []}},
    {{"title": "LANGUAGES", "type": "list", "items": []}}
  ]
}}
Rules: Keep ALL real info. No inventions. Return ONLY JSON.

CV:
{cv_texto}"""
    else:
        prompt = f"""Eres un experto redactor de CVs. Restructura y mejora este CV.
Devuelve SOLO un objeto JSON válido con esta estructura exacta:
{{
  "name": "Nombre completo",
  "title": "Título profesional",
  "profile": "Perfil profesional (3-4 frases)",
  "contact": {{
    "email": "", "phone": "", "location": "", "linkedin": "", "github": ""
  }},
  "sections": [
    {{"title": "EXPERIENCIA", "type": "timeline", "items": [{{"title": "", "subtitle": "", "date": "", "bullets": []}}]}},
    {{"title": "PROYECTOS", "type": "timeline", "items": [{{"title": "", "subtitle": "", "date": "", "bullets": []}}]}},
    {{"title": "FORMACIÓN", "type": "timeline", "items": [{{"title": "", "subtitle": "", "date": "", "bullets": []}}]}},
    {{"title": "HABILIDADES", "type": "chips", "items": []}},
    {{"title": "IDIOMAS", "type": "list", "items": []}}
  ]
}}
Reglas: Mantén TODA la información real. No inventes nada. Devuelve SOLO el JSON.

CV:
{cv_texto}"""

    texto = _llamar_groq(prompt, max_tokens=3000, token=token)
    texto = re.sub(r'```json\s*', '', texto)
    texto = re.sub(r'```\s*', '', texto)
    texto = texto.strip()

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]+\}', texto)
        if match:
            return json.loads(match.group())
        raise Exception('La IA no devolvió un JSON válido. Inténtalo de nuevo.')