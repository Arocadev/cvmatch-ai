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

def analizar_oferta_para_cv(descripcion_oferta, cv_texto):
    prompt = f"""Eres un experto en selección de personal y optimización de CVs para sistemas ATS.

Tengo esta oferta de trabajo:
{descripcion_oferta}

Este es mi CV actual:
{cv_texto}

Responde en este formato exacto:

COMPATIBILIDAD: X%
(donde X es un número del 0 al 100 indicando cuánto encaja mi CV con esta oferta)

RESUMEN:
(2-3 frases explicando por qué ese porcentaje)

PALABRAS CLAVE QUE FALTAN:
(lista de palabras clave de la oferta que no aparecen en mi CV)

QUÉ DESTACAR:
(qué experiencias o habilidades de mi CV son más relevantes para esta oferta)

CAMBIOS CONCRETOS:
(cambios específicos que debo hacer en mi CV para esta oferta)

Sé directo y específico, no genérico."""

    respuesta = cliente.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=1000,
    )
    
    return respuesta.choices[0].message.content

def generar_cv_adaptado(descripcion_oferta, cv_texto):
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