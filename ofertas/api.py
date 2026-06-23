import requests
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv('ADZUNA_APP_ID')
APP_KEY = os.getenv('ADZUNA_APP_KEY')

def buscar_ofertas(keywords='devops', ubicacion='Valencia', pagina=1, full_time=None, salary_min=None, experience=None):
    url = f'https://api.adzuna.com/v1/api/jobs/es/search/{pagina}'
    
    params = {
        'app_id': APP_ID,
        'app_key': APP_KEY,
        'what': keywords,
        'where': ubicacion,
        'results_per_page': 20,
        'content-type': 'application/json',
    }
    
    if salary_min:
        params['salary_min'] = salary_min
    
    if full_time:
        params['full_time'] = 1
    
    response = requests.get(url, params=params)
    return response.json()