from django.core.management.base import BaseCommand
from empresa.models_simulaciones import TipoSimulacion

class Command(BaseCommand):
    help = 'Crea los tipos de simulación iniciales'

    def handle(self, *args, **options):
        # Limpiar datos existentes
        TipoSimulacion.objects.all().delete()
        
        # SIMULACIONES POR CATEGORÍA
        simulaciones = [
            {
                'nombre': 'Simulación de Venta',
                'categoria': 'comercial',
                'descripcion': 'Practica registrando ventas y calculando totales con IVA',
                'icono': 'fas fa-cash-register',
                'configuracion': {
                    'campos_requeridos': ['producto', 'cantidad', 'precio_unitario', 'subtotal', 'iva', 'total'],
                    'validaciones': ['calculos_correctos', 'iva_12_porciento'],
                    'puntuacion_maxima': 100
                }
            },
            {
                'nombre': 'Simulación de Receta',
                'categoria': 'manufactura',
                'descripcion': 'Crea recetas de producción y calcula costos de materias primas',
                'icono': 'fas fa-clipboard-list',
                'configuracion': {
                    'campos_requeridos': ['producto_nombre', 'ingredientes', 'costo_total', 'precio_venta'],
                    'validaciones': ['costo_correcto', 'margen_adecuado'],
                    'puntuacion_maxima': 100
                }
            },
            {
                'nombre': 'Simulación de Servicio',
                'categoria': 'servicios',
                'descripcion': 'Factura servicios profesionales calculando horas y tarifas',
                'icono': 'fas fa-handshake',
                'configuracion': {
                    'campos_requeridos': ['tipo_servicio', 'horas_trabajadas', 'tarifa_hora', 'subtotal', 'iva', 'total'],
                    'validaciones': ['calculos_correctos', 'tarifa_competitiva'],
                    'puntuacion_maxima': 100
                }
            }
        ]
        
        for sim_data in simulaciones:
            TipoSimulacion.objects.create(**sim_data)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Creados {len(simulaciones)} tipos de simulación')
        )