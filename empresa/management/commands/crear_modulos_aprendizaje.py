from django.core.management.base import BaseCommand
from empresa.models import ModuloAprendizaje, Leccion

class Command(BaseCommand):
    help = 'Crea los módulos de aprendizaje iniciales'

    def handle(self, *args, **options):
        # Limpiar datos existentes
        ModuloAprendizaje.objects.all().delete()
        
        # MÓDULOS PARA COMERCIO
        modulo_comercio = ModuloAprendizaje.objects.create(
            nombre="Primeros Pasos en Comercio",
            tipo_empresa="comercial",
            nivel=1,
            descripcion="Aprende los conceptos básicos para gestionar tu negocio comercial",
            icono="fas fa-store",
            orden=1
        )
        
        # Lecciones para comercio
        Leccion.objects.create(
            modulo=modulo_comercio,
            titulo="¿Qué es una venta?",
            tipo="teoria",
            contenido="Una venta es el intercambio de un producto o servicio por dinero. En CONTAFY registramos cada venta para llevar control de nuestros ingresos.",
            puntos_xp=10,
            tiempo_estimado=5,
            orden=1
        )
        
        Leccion.objects.create(
            modulo=modulo_comercio,
            titulo="Registra tu primera venta",
            tipo="practica",
            contenido="Vamos a registrar una venta paso a paso. Necesitarás: cliente, producto, cantidad y precio.",
            puntos_xp=20,
            tiempo_estimado=10,
            orden=2
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
        
        # Lecciones para manufactura
        Leccion.objects.create(
            modulo=modulo_manufactura,
            titulo="¿Qué son las materias primas?",
            tipo="teoria",
            contenido="Las materias primas son los ingredientes o materiales que usas para crear tus productos. Controlar su costo es clave para la rentabilidad.",
            puntos_xp=10,
            tiempo_estimado=5,
            orden=1
        )
        
        Leccion.objects.create(
            modulo=modulo_manufactura,
            titulo="Crea tu primera receta",
            tipo="practica",
            contenido="Una receta define qué materias primas necesitas y en qué cantidad para crear un producto.",
            puntos_xp=20,
            tiempo_estimado=15,
            orden=2
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
        
        # Lecciones para servicios
        Leccion.objects.create(
            modulo=modulo_servicios,
            titulo="¿Cómo facturar un servicio?",
            tipo="teoria",
            contenido="Facturar servicios es diferente a vender productos. Aquí el tiempo y la experiencia son tu valor principal.",
            puntos_xp=10,
            tiempo_estimado=5,
            orden=1
        )
        
        Leccion.objects.create(
            modulo=modulo_servicios,
            titulo="Registra tu primer servicio",
            tipo="practica",
            contenido="Vamos a crear un tipo de servicio y facturar tu primera prestación de servicio.",
            puntos_xp=20,
            tiempo_estimado=10,
            orden=2
        )
        
        self.stdout.write(
            self.style.SUCCESS('✓ Módulos de aprendizaje creados exitosamente')
        )