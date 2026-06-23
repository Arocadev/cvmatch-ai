from django.core.management.base import BaseCommand
from ofertas.api import buscar_ofertas
from ofertas.models import Oferta
from datetime import datetime

class Command(BaseCommand):
    help = 'Importa ofertas de empleo desde Adzuna'

    def handle(self, *args, **kwargs):
        self.stdout.write('Buscando ofertas...')
        
        resultado = buscar_ofertas()
        ofertas = resultado.get('results', [])
        
        nuevas = 0
        for item in ofertas:
            oferta_id = item.get('id')
            
            # Si ya existe en la BD, la saltamos
            if Oferta.objects.filter(url_original__contains=oferta_id).exists():
                continue
            
            Oferta.objects.create(
                titulo=item.get('title', ''),
                empresa=item['company'].get('display_name', ''),
                ubicacion=item['location'].get('display_name', ''),
                descripcion=item.get('description', ''),
                url_original=item.get('redirect_url', ''),
                fecha_publicacion=datetime.strptime(
                    item['created'][:10], '%Y-%m-%d'
                ).date(),
            )
            nuevas += 1
        
        self.stdout.write(f'{nuevas} ofertas nuevas importadas.')