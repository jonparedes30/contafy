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
            titulo="Práctica: Crear tu primer producto",
            tipo="practica",
            contenido="Ahora vamos a crear un producto en CONTAFY paso a paso:\n\n1. Ve a 'Inventario > Ver Productos'\n2. Haz clic en '+ Nuevo Producto'\n3. Completa: Nombre, Código, Precio de compra, PVP, Stock\n4. Ejemplo: Camiseta Polo, código CAM001, compra $8, venta $15, stock 50\n\nEsto te permitirá tener productos listos para vender.",
            puntos_xp=15,
            tiempo_estimado=8,
            orden=2
        )
        
        Leccion.objects.create(
            modulo=modulo_comercio,
            titulo="Práctica: Registrar una venta real",
            tipo="practica",
            contenido="Ahora registremos una venta usando el producto que creaste:\n\n1. Ve a 'Transacciones > + Nueva Venta'\n2. Selecciona el producto que creaste\n3. Ingresa cantidad: 2 unidades\n4. El sistema calculará automáticamente el total\n5. Selecciona tipo de pago: 'contado'\n6. Guarda la venta\n\n¡Felicidades! Has registrado tu primera venta y el stock se actualizó automáticamente.",
            puntos_xp=25,
            tiempo_estimado=10,
            orden=3
        )
        
        Leccion.objects.create(
            modulo=modulo_comercio,
            titulo="Simulación: Calculadora de IVA",
            tipo="simulacion",
            contenido="Practica calculando el IVA con diferentes productos y cantidades. Esta simulación te ayudará a dominar los cálculos antes de hacerlo en el sistema real.",
            puntos_xp=20,
            tiempo_estimado=12,
            orden=4
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
            titulo="Práctica: Registrar materias primas",
            tipo="practica",
            contenido="Vamos a registrar materias primas en CONTAFY:\n\n1. Ve a 'Materias Primas > + Nueva Materia Prima'\n2. Ejemplo: Harina, unidad 'kg', precio $1.50\n3. Registra al menos 3 materias primas\n4. Estas serán la base para crear tus productos\n\nEsto te permitirá controlar costos de producción.",
            puntos_xp=15,
            tiempo_estimado=10,
            orden=2
        )
        
        Leccion.objects.create(
            modulo=modulo_manufactura,
            titulo="Práctica: Crear producto manufacturado",
            tipo="practica",
            contenido="Ahora creemos un producto con receta:\n\n1. Ve a 'Catálogo > + Nuevo Producto'\n2. Ejemplo: Pan Integral\n3. Agrega materias primas: Harina 0.5kg, Azúcar 0.1kg\n4. El sistema calculará el costo automáticamente\n5. Define precio de venta con margen de ganancia\n\n¡Ya tienes tu primer producto manufacturado!",
            puntos_xp=25,
            tiempo_estimado=15,
            orden=3
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
            titulo="Práctica: Crear tipos de servicios",
            tipo="practica",
            contenido="Vamos a configurar tus servicios en CONTAFY:\n\n1. Ve a 'Servicios > + Nuevo Servicio'\n2. Ejemplo: Consultoría, precio $25/hora\n3. Crea al menos 2 tipos de servicios\n4. Define precios por hora o por proyecto\n\nEsto te permitirá facturar rápidamente.",
            puntos_xp=15,
            tiempo_estimado=8,
            orden=2
        )
        
        Leccion.objects.create(
            modulo=modulo_servicios,
            titulo="Práctica: Facturar un servicio",
            tipo="practica",
            contenido="Ahora facturemos un servicio:\n\n1. Ve a 'Servicios > + Nueva Factura'\n2. Selecciona el servicio creado\n3. Ingresa horas trabajadas: 3 horas\n4. El sistema calculará el total\n5. Agrega gastos adicionales si los hay\n6. Guarda la factura\n\n¡Has facturado tu primer servicio!",
            puntos_xp=25,
            tiempo_estimado=12,
            orden=3
        )
        
        self.stdout.write(
            self.style.SUCCESS('✓ Módulos de aprendizaje creados exitosamente')
        )