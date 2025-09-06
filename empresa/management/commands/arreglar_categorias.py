from django.core.management.base import BaseCommand
from empresa.models import Empresa, CategoriaProducto, Producto

class Command(BaseCommand):
    help = 'Arregla las categorías de productos faltantes'

    def handle(self, *args, **options):
        empresas = Empresa.objects.all()
        
        for empresa in empresas:
            # Crear categoría General si no existe
            categoria_general, created = CategoriaProducto.objects.get_or_create(
                empresa=empresa,
                nombre='General',
                defaults={'descripcion': 'Categoría general para productos'}
            )
            
            if created:
                self.stdout.write(f'✅ Creada categoría General para {empresa.nombre}')
            
            # Asignar categoría General a productos sin categoría
            productos_sin_categoria = Producto.objects.filter(
                empresa=empresa,
                categoria__isnull=True
            )
            
            if productos_sin_categoria.exists():
                productos_sin_categoria.update(categoria=categoria_general)
                self.stdout.write(f'✅ Asignada categoría General a {productos_sin_categoria.count()} productos de {empresa.nombre}')
        
        self.stdout.write(self.style.SUCCESS('✅ Categorías arregladas correctamente'))