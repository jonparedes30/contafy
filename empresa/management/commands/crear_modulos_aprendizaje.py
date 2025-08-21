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
        
        # Lección integrada para comercio con pasos JSON
        Leccion.objects.create(
            modulo=modulo_comercio,
            titulo="Domina las Ventas: De la Teoría a la Práctica",
            tipo="practica",
            contenido="Una venta es el intercambio de un producto por dinero. En CONTAFY cada venta se registra automáticamente y actualiza tu inventario.",
            pasos=[
                {
                    "tipo": "teoria",
                    "titulo": "💰 Concepto de Venta",
                    "contenido": "Una venta es el intercambio de un producto por dinero. En CONTAFY cada venta se registra automáticamente.",
                    "micro_xp": 5
                },
                {
                    "tipo": "practica",
                    "titulo": "📦 Paso 1: Crear Producto",
                    "contenido": "Vamos a agregar un producto a tu inventario",
                    "instrucciones": "Ve a Inventario > + Nuevo Producto y crea una Camiseta Polo por $15",
                    "micro_xp": 10
                },
                {
                    "tipo": "practica",
                    "titulo": "💵 Paso 2: Registrar Venta",
                    "contenido": "Ahora vamos a vender el producto que acabas de crear",
                    "instrucciones": "Ve a Transacciones > + Nueva Venta y vende 2 Camisetas Polo",
                    "micro_xp": 15
                },
                {
                    "tipo": "quiz",
                    "titulo": "🤔 Quiz: Cálculo de Venta",
                    "pregunta": "¿Cuál es el total de vender 2 camisetas a $15 cada una?",
                    "opciones": ["$25", "$30", "$35"],
                    "respuesta_correcta": 1,
                    "micro_xp": 20
                }
            ],
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
        
        # Lección integrada para manufactura con pasos JSON
        Leccion.objects.create(
            modulo=modulo_manufactura,
            titulo="Domina la Producción: Materias Primas y Productos",
            tipo="practica",
            contenido="La manufactura combina materias primas para crear productos. En CONTAFY controlas costos y recetas automáticamente.",
            pasos=[
                {
                    "tipo": "teoria",
                    "titulo": "🏭 Concepto de Manufactura",
                    "contenido": "La manufactura combina materias primas para crear productos. En CONTAFY controlas costos y recetas.",
                    "micro_xp": 5
                },
                {
                    "tipo": "practica",
                    "titulo": "🌾 Paso 1: Registrar Materias Primas",
                    "contenido": "Primero necesitas los ingredientes para tus productos",
                    "instrucciones": "Ve a Materias Primas > + Nueva y registra: Harina (kg) $1.50, Azúcar (kg) $2.00",
                    "micro_xp": 10
                },
                {
                    "tipo": "practica",
                    "titulo": "🍞 Paso 2: Crear Producto con Receta",
                    "contenido": "Ahora crea un producto usando las materias primas",
                    "instrucciones": "Ve a Catálogo > + Nuevo Producto y crea Pan con receta: 0.5kg Harina + 0.1kg Azúcar",
                    "micro_xp": 15
                },
                {
                    "tipo": "quiz",
                    "titulo": "💰 Quiz: Cálculo de Costo",
                    "pregunta": "Si usas 0.5kg de Harina ($1.50/kg) y 0.1kg de Azúcar ($2.00/kg), ¿cuál es el costo?",
                    "opciones": ["$0.75", "$0.95", "$1.20"],
                    "respuesta_correcta": 1,
                    "micro_xp": 20
                }
            ],
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
        
        # Lección integrada para servicios con pasos JSON
        Leccion.objects.create(
            modulo=modulo_servicios,
            titulo="Domina los Servicios: Crear y Facturar",
            tipo="practica",
            contenido="Los servicios se facturan por tiempo o proyecto. En CONTAFY puedes gestionar servicios profesionales fácilmente.",
            pasos=[
                {
                    "tipo": "teoria",
                    "titulo": "💼 Concepto de Servicios",
                    "contenido": "Los servicios se facturan por tiempo o proyecto. En CONTAFY puedes gestionar servicios profesionales.",
                    "micro_xp": 5
                },
                {
                    "tipo": "practica",
                    "titulo": "⚙️ Paso 1: Crear Tipo de Servicio",
                    "contenido": "Define qué servicios ofreces y sus precios",
                    "instrucciones": "Ve a Servicios > + Nuevo Servicio y crea: Consultoría $25/hora",
                    "micro_xp": 10
                },
                {
                    "tipo": "practica",
                    "titulo": "📊 Paso 2: Facturar un Servicio",
                    "contenido": "Ahora factura el servicio que acabas de crear",
                    "instrucciones": "Ve a Servicios > + Nueva Factura y factura 3 horas de Consultoría",
                    "micro_xp": 15
                },
                {
                    "tipo": "quiz",
                    "titulo": "🕰️ Quiz: Cálculo de Servicio",
                    "pregunta": "¿Cuánto cobrarías por 3 horas de consultoría a $25/hora?",
                    "opciones": ["$65", "$75", "$85"],
                    "respuesta_correcta": 1,
                    "micro_xp": 20
                }
            ],
            puntos_xp=50,
            tiempo_estimado=15,
            orden=1
        )
        
        self.stdout.write(
            self.style.SUCCESS('✓ Módulos de aprendizaje creados exitosamente')
        )