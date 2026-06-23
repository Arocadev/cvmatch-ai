import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

cliente = Groq(api_key=os.getenv('GROQ_API_KEY'))

def analizar_oferta_para_cv(descripcion_oferta, cv_texto):
    prompt = f"""Eres un experto en selección de personal y optimización de CVs para sistemas ATS.
    
Tengo esta oferta de trabajo:
{descripcion_oferta}

Este es mi CV actual:
{cv_texto}

Dame recomendaciones concretas y específicas para adaptar mi CV a esta oferta:
1. Palabras clave que debo incluir
2. Qué experiencias o habilidades destacar más
3. Qué cambios concretos hacer en el CV
4. Cómo mejorar mi CV para pasar los filtros ATS de esta oferta

Sé directo y específico, no genérico."""

    respuesta = cliente.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=1000,
    )
    
    return respuesta.choices[0].message.content

