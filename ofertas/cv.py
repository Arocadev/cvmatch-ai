import os
import fitz
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

cliente = Groq(api_key=os.getenv('GROQ_API_KEY'))

def extraer_texto_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texto = ''
    for page in doc:
        texto += page.get_text()
    return texto

def resumir_oferta(descripcion_oferta, idioma='es'):
    if idioma == 'en':
        prompt = f"""Analyze this job offer and extract the key information in this exact format:

POSITION: (job title)
COMPANY: (company name if available)
MODALITY: (Remote / Hybrid / On-site / Not specified)
EXPERIENCE: (years required or Not specified)
SALARY: (range if available or Not specified)
STACK: (main technologies and tools, separated by commas)
SUMMARY: (2-3 sentences explaining what the role is about and what they are looking for)

Job offer:
{descripcion_oferta}

Respond ONLY with the format above, nothing else."""
    else:
        prompt = f"""Analiza esta oferta de trabajo y extrae la información clave en este formato exacto:

PUESTO: (título del puesto)
EMPRESA: (nombre de la empresa si aparece)
MODALIDAD: (Remoto / Híbrido / Presencial / No especificado)
EXPERIENCIA: (años requeridos o No especificado)
SALARIO: (rango si aparece o No especificado)
STACK: (tecnologías y herramientas principales, separadas por comas)
RESUMEN: (2-3 frases explicando de qué trata el puesto y qué buscan)

Oferta:
{descripcion_oferta}

Responde SOLO con el formato indicado, sin añadir nada más."""

    respuesta = cliente.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=500,
    )
    
    return respuesta.choices[0].message.content

def analizar_oferta_para_cv(descripcion_oferta, cv_texto, idioma='es'):
    if idioma == 'en':
        prompt = f"""You are an expert in recruitment and ATS CV optimization.

Job offer:
{descripcion_oferta}

My current CV:
{cv_texto}

Analyze the level of the offer (junior, mid, senior) and take it into account.
Do not ask for experience beyond the level of the offer.

Respond in this exact format:

COMPATIBILITY: X%
(where X is a number from 0 to 100 indicating how well my CV matches this offer)

OFFER LEVEL: (Junior/Mid/Senior)

SUMMARY:
(2-3 sentences explaining why that percentage, considering the level)

MISSING KEYWORDS:
(only the relevant ones for the offer level)

WHAT TO HIGHLIGHT:
(which experiences or skills from my CV are most relevant for this specific offer)

CONCRETE CHANGES:
(specific and realistic changes for my level)

Be direct, specific and realistic about the candidate's experience level."""
    else:
        prompt = f"""Eres un experto en selección de personal y optimización de CVs para sistemas ATS.

Tengo esta oferta de trabajo:
{descripcion_oferta}

Este es mi CV actual:
{cv_texto}

Analiza el nivel de la oferta (junior, mid, senior) y tenlo en cuenta en tu análisis.
No me pidas experiencia que no corresponda al nivel de la oferta.

Responde en este formato exacto:

COMPATIBILIDAD: X%
(donde X es un número del 0 al 100 indicando cuánto encaja mi CV con esta oferta)

NIVEL DE LA OFERTA: (Junior/Mid/Senior)

RESUMEN:
(2-3 frases explicando por qué ese porcentaje, teniendo en cuenta el nivel)

PALABRAS CLAVE QUE FALTAN:
(solo las relevantes para el nivel de la oferta)

QUÉ DESTACAR:
(qué experiencias o habilidades de mi CV son más relevantes para esta oferta concreta)

CAMBIOS CONCRETOS:
(cambios específicos y realistas para mi nivel)

Sé directo, específico y realista con el nivel de experiencia del candidato."""

    respuesta = cliente.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=1000,
    )
    
    return respuesta.choices[0].message.content

def generar_cv_adaptado(descripcion_oferta, cv_texto, idioma='es'):
    if idioma == 'en':
        prompt = f"""You are an expert in CV writing and ATS optimization.

Job offer:
{descripcion_oferta}

My current CV:
{cv_texto}

Rewrite my complete CV adapted to this offer. Rules:
- Keep ALL the real information in my CV, do not invent anything
- Reorganize, rephrase and highlight what is most relevant for this offer
- Add the offer's keywords where they fit naturally
- Improve the wording of each section to sound more professional
- Keep the same section format (Education, Experience, Projects, Skills, Languages)

Return ONLY the rewritten CV, no explanations or comments."""
    else:
        prompt = f"""Eres un experto en redacción de CVs y optimización ATS.

Tengo esta oferta de trabajo:
{descripcion_oferta}

Este es mi CV actual:
{cv_texto}

Reescribe mi CV completo adaptado a esta oferta. Reglas:
- Mantén TODA la información real que hay en mi CV, no inventes nada
- Reorganiza, reformula y destaca lo más relevante para esta oferta
- Añade las palabras clave de la oferta donde encajen de forma natural
- Mejora la redacción de cada sección para que suene más profesional
- Mantén el mismo formato de secciones (Estudios, Experiencia, Proyectos, Habilidades, Idiomas)

Devuelve SOLO el CV reescrito, sin explicaciones ni comentarios."""

    respuesta = cliente.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=2000,
    )
    
    return respuesta.choices[0].message.content