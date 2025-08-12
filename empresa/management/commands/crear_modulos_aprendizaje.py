from django.core.management.base import BaseCommand
from empresa.models import ModuloAprendizaje, Leccion

class Command(BaseCommand):
    help = 'Crea los módulos de aprendizaje iniciales'

    def handle(self, *args, **options):
        # Limpiar datos existentes si las tablas existen
        try:
            ModuloAprendizaje.objects.all().delete()
        except Exception:
            pass  # Las tablas no existen aún
        
        # MÓDULOS PARA COMERCIO
        modulo_comercio = ModuloAprendizaje.objects.create(
            nombre="Primeros Pasos en Comercio",
            tipo_empresa="comercial",
            nivel=1,
            descripcion="Aprende los conceptos básicos para gestionar tu negocio comercial",
            icono="fas fa-store",
            orden=1
        )
        
        # Lección integrada para comercio
        Leccion.objects.create(
            modulo=modulo_comercio,
            titulo="Domina las Ventas: De la Teoría a la Práctica",
            tipo="practica",
            contenido="INTERACTIVE_LESSON",
            puntos_xp=50,
            tiempo_estimado=15,
            orden=1
        )
        
        # MÓDULOS PARA MANUFACTURA
        modulo_manufactura = ModuloAprendizaje.objects.create(
            nombre="Fundamentos de Manufactura",
            tipo_empresa="manufactura",
            nivel=1,
            descripcion="Domina los conceptos de producción y costos en tu negocio manufacturero",
            icono="fas fa-industry",
            orden=1
        )
        
        # Lección integrada para manufactura
        Leccion.objects.create(
            modulo=modulo_manufactura,
            titulo="Domina la Producción: Materias Primas y Productos",
            tipo="practica",
            contenido="INTERACTIVE_LESSON",
            puntos_xp=50,
            tiempo_estimado=15,
            orden=1
        )
        
        # MÓDULOS PARA SERVICIOS
        modulo_servicios = ModuloAprendizaje.objects.create(
            nombre="Gestión de Servicios",
            tipo_empresa="servicios",
            nivel=1,
            descripcion="Aprende a facturar y gestionar tu negocio de servicios profesionales",
            icono="fas fa-handshake",
            orden=1
        )
        
        # Lección integrada para servicios
        Leccion.objects.create(
            modulo=modulo_servicios,
            titulo="Domina los Servicios: Crear y Facturar",
            tipo="practica",
            contenido="INTERACTIVE_LESSON",
            puntos_xp=50,
            tiempo_estimado=15,
            orden=1
        )
        
        self.stdout.write(
            self.style.SUCCESS('✓ Módulos de aprendizaje creados exitosamente')
        )