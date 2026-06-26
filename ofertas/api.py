import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID = os.getenv('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.getenv('ADZUNA_APP_KEY')
JOOBLE_API_KEY = os.getenv('JOOBLE_API_KEY')

def buscar_adzuna(keywords='devops', ubicacion='Valencia', pais='es', salary_min=None, pagina=1):
    url = f'https://api.adzuna.com/v1/api/jobs/{pais}/search/{pagina}'
    params = {
        'app_id': ADZUNA_APP_ID,
        'app_key': ADZUNA_APP_KEY,
        'what': keywords,
        'where': ubicacion,
        'results_per_page': 20,
        'content-type': 'application/json',
    }
    if salary_min:
        params['salary_min'] = salary_min
    response = requests.get(url, params=params)
    return response.json().get('results', [])

def buscar_jooble(keywords='devops', ubicacion='Valencia', pagina=1):
    url = f'https://jooble.org/api/{JOOBLE_API_KEY}'
    payload = {
        'keywords': keywords,
        'location': ubicacion,
        'page': pagina,
    }
    response = requests.post(url, json=payload)
    return response.json().get('jobs', [])

def buscar_arbeitnow(keywords='devops', pagina=1):
    url = 'https://www.arbeitnow.com/api/job-board-api'
    params = {
        'search': keywords,
        'page': pagina,
    }
    response = requests.get(url, params=params)
    return response.json().get('data', [])

def buscar_ofertas(keywords='devops', ubicacion='Valencia', fuente='adzuna_es', salary_min=None, pagina=1):
    if fuente == 'adzuna_es':
        return buscar_adzuna(keywords, ubicacion, 'es', salary_min, pagina)
    elif fuente == 'adzuna_uk':
        return buscar_adzuna(keywords, ubicacion, 'gb', salary_min, pagina)
    elif fuente == 'adzuna_us':
        return buscar_adzuna(keywords, ubicacion, 'us', salary_min, pagina)
    elif fuente == 'jooble':
        return buscar_jooble(keywords, ubicacion, pagina)
    elif fuente == 'arbeitnow':
        return buscar_arbeitnow(keywords, pagina)
    elif fuente == 'todas':
        resultados = []
        for item in buscar_adzuna(keywords, ubicacion, 'es', salary_min, pagina):
            resultados.append({
                'id': item.get('id', ''),
                'titulo': item.get('title', ''),
                'empresa': item.get('company', {}).get('display_name', ''),
                'ubicacion': item.get('location', {}).get('display_name', ''),
                'descripcion': item.get('description', ''),
                'url_original': item.get('redirect_url', ''),
                'fecha': datetime.strptime(item['created'][:10], '%Y-%m-%d').date(),
                'fuente': 'adzuna_es'
            })
        for item in buscar_jooble(keywords, ubicacion, pagina):
            fecha_str = item.get('updated', '')[:10]
            resultados.append({
                'id': str(item.get('id', '')),
                'titulo': item.get('title', ''),
                'empresa': item.get('company', ''),
                'ubicacion': item.get('location', ''),
                'descripcion': item.get('snippet', ''),
                'url_original': item.get('link', ''),
                'fecha': datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.now().date(),
                'fuente': 'jooble'
            })
        for item in buscar_arbeitnow(keywords, pagina):
            timestamp = item.get('created_at', 0)
            resultados.append({
                'id': item.get('slug', ''),
                'titulo': item.get('title', ''),
                'empresa': item.get('company_name', ''),
                'ubicacion': item.get('location', ''),
                'descripcion': item.get('description', ''),
                'url_original': item.get('url', ''),
                'fecha': datetime.fromtimestamp(timestamp).date() if timestamp else datetime.now().date(),
                'fuente': 'arbeitnow'
            })
        return resultados
    return []