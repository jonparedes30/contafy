from django.core.management.base import BaseCommand
from empresa.models import Empresa
from decimal import Decimal

class Command(BaseCommand):
    help = 'Agrega coordenadas GPS a las empresas existentes'

    def handle(self, *args, **options):
        # Coordenadas aproximadas de ciudades ecuatorianas
        coordenadas_ciudades = {
            'Quito': (-0.1807, -78.4678),
            'Guayaquil': (-2.1894, -79.8890),
            'Cuenca': (-2.9001, -79.0059),
            'Ambato': (-1.2490, -78.6067),
            'Machala': (-3.2581, -79.9553),
            'Manta': (-0.9677, -80.7089),
        }
        
        empresas_actualizadas = 0
        
        for empresa in Empresa.objects.all():
            if empresa.ciudad and not (empresa.latitud and empresa.longitud):
                ciudad_key = empresa.ciudad.title()
                if ciudad_key in coordenadas_ciudades:
                    lat, lng = coordenadas_ciudades[ciudad_key]
                    # Agregar variación pequeña para simular ubicaciones diferentes
                    import random
                    variacion = 0.01  # ~1km de variación
                    lat_final = lat + random.uniform(-variacion, variacion)
                    lng_final = lng + random.uniform(-variacion, variacion)
                    
                    empresa.latitud = Decimal(str(round(lat_final, 6)))
                    empresa.longitud = Decimal(str(round(lng_final, 6)))
                    empresa.save()
                    
                    self.stdout.write(f'GPS agregado a {empresa.nombre}: {lat_final:.4f}, {lng_final:.4f}')
                    empresas_actualizadas += 1
        
        self.stdout.write(self.style.SUCCESS(f'Coordenadas GPS agregadas a {empresas_actualizadas} empresas'))