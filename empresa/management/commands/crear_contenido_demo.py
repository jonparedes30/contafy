from django.core.management.base import BaseCommand
from django.utils.text import slugify
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion
from empresa.models_simulaciones import TipoSimulacion, EscenarioSimulacion

class Command(BaseCommand):
    help = 'Crea contenido demo para la Academia CONTAFY'

    def handle(self, *args, **options):
        self.stdout.write('Creando contenido demo para Academia CONTAFY...')
        
        # Crear módulos por tipo de empresa
        modulos_data = [
            {
                'nombre': 'Fundamentos Contables',
                'tipo_empresa': 'comercial',
                'nivel': 1,
                'descripcion': 'Conceptos básicos de contabilidad para empresas comerciales',
                'orden': 1
            },
            {
                'nombre': 'Gestión de Inventarios',
                'tipo_empresa': 'comercial', 
                'nivel': 2,
                'descripcion': 'Control y manejo de inventarios comerciales',
                'orden': 2
            },
            {
                'nombre': 'Contabilidad de Costos',
                'tipo_empresa': 'manufactura',
                'nivel': 1,
                'descripcion': 'Fundamentos de costos en manufactura',
                'orden': 1
            },
            {
                'nombre': 'Facturación de Servicios',
                'tipo_empresa': 'servicios',
                'nivel': 1,
                'descripcion': 'Manejo contable de empresas de servicios',
                'orden': 1
            }
        ]
        
        for modulo_data in modulos_data:
            modulo, created = ModuloAprendizaje.objects.get_or_create(
                slug=slugify(modulo_data['nombre']),
                defaults=modulo_data
            )
            if created:
                self.stdout.write(f'[OK] Módulo creado: {modulo.nombre}')
                
                # Crear lecciones para cada módulo
                self.crear_lecciones_modulo(modulo)
        
        # Crear tipos de simulación
        self.crear_tipos_simulacion()
        
        self.stdout.write(self.style.SUCCESS('[OK] Contenido demo creado exitosamente'))

    def crear_lecciones_modulo(self, modulo):
        """Crea lecciones específicas para cada módulo"""
        
        if modulo.tipo_empresa == 'comercial':
            lecciones = [
                {
                    'titulo': 'Qué es la Contabilidad',
                    'tipo': 'teoria',
                    'contenido': 'La contabilidad es el sistema de información que registra las operaciones económicas de una empresa.',
                    'pasos': [
                        {'titulo': 'Concepto', 'descripcion': 'Aprende qué es la contabilidad', 'accion': 'leer'},
                        {'titulo': 'Importancia', 'descripcion': 'Por qué es importante llevar contabilidad', 'accion': 'leer'},
                        {'titulo': 'Quiz', 'descripcion': '¿Qué es la contabilidad?', 'accion': 'quiz', 'datos': {'pregunta': '¿Qué es la contabilidad?', 'opciones': ['Sistema de información', 'Solo números', 'Impuestos'], 'correcta': 0}}
                    ],
                    'puntos_xp': 15,
                    'tiempo_estimado': 5,
                    'orden': 1
                },
                {
                    'titulo': 'Registro de Ventas',
                    'tipo': 'simulacion',
                    'contenido': 'Aprende a registrar una venta paso a paso.',
                    'pasos': [
                        {'titulo': 'Preparación', 'descripcion': 'Datos necesarios para registrar una venta', 'accion': 'leer'},
                        {'titulo': 'Simulación', 'descripcion': 'Registra tu primera venta', 'accion': 'simulacion', 'datos': {'tipo': 'venta'}}
                    ],
                    'puntos_xp': 25,
                    'tiempo_estimado': 10,
                    'orden': 2
                }
            ]
        elif modulo.tipo_empresa == 'manufactura':
            lecciones = [
                {
                    'titulo': 'Costos de Producción',
                    'tipo': 'teoria',
                    'contenido': 'Tipos de costos en la manufactura: materiales, mano de obra y gastos indirectos.',
                    'pasos': [
                        {'titulo': 'Materiales', 'descripcion': 'Costos de materias primas', 'accion': 'leer'},
                        {'titulo': 'Mano de obra', 'descripcion': 'Costos de personal de producción', 'accion': 'leer'}
                    ],
                    'puntos_xp': 20,
                    'tiempo_estimado': 8,
                    'orden': 1
                }
            ]
        else:  # servicios
            lecciones = [
                {
                    'titulo': 'Facturación de Servicios',
                    'tipo': 'practica',
                    'contenido': 'Cómo facturar servicios profesionales correctamente.',
                    'pasos': [
                        {'titulo': 'Tipos de servicios', 'descripcion': 'Clasificación de servicios', 'accion': 'leer'},
                        {'titulo': 'Práctica', 'descripcion': 'Crea tu primera factura de servicio', 'accion': 'simulacion', 'datos': {'tipo': 'servicio'}}
                    ],
                    'puntos_xp': 20,
                    'tiempo_estimado': 7,
                    'orden': 1
                }
            ]
        
        for leccion_data in lecciones:
            leccion, created = Leccion.objects.get_or_create(
                modulo=modulo,
                slug=slugify(leccion_data['titulo']),
                defaults=leccion_data
            )
            if created:
                self.stdout.write(f'  [OK] Lección: {leccion.titulo}')

    def crear_tipos_simulacion(self):
        """Crea tipos de simulación y escenarios"""
        
        tipos_data = [
            {
                'nombre': 'Registro de Venta',
                'categoria': 'comercial',
                'descripcion': 'Simulación de registro de ventas comerciales',
                'configuracion': {'permite_descuentos': True, 'iva_incluido': True}
            },
            {
                'nombre': 'Orden de Producción',
                'categoria': 'manufactura', 
                'descripcion': 'Simulación de órdenes de producción',
                'configuracion': {'calcula_costos': True, 'materiales_requeridos': True}
            },
            {
                'nombre': 'Factura de Servicio',
                'categoria': 'servicios',
                'descripcion': 'Simulación de facturación de servicios',
                'configuracion': {'horas_trabajadas': True, 'tarifa_hora': True}
            }
        ]
        
        for tipo_data in tipos_data:
            tipo, created = TipoSimulacion.objects.get_or_create(
                nombre=tipo_data['nombre'],
                categoria=tipo_data['categoria'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(f'[OK] Tipo simulación: {tipo.nombre}')
                
                # Crear escenarios para cada tipo
                self.crear_escenarios_tipo(tipo)

    def crear_escenarios_tipo(self, tipo):
        """Crea escenarios específicos para cada tipo de simulación"""
        
        if tipo.categoria == 'comercial':
            escenarios = [
                {
                    'nombre': 'Venta Simple',
                    'descripcion': 'Venta básica de un producto',
                    'datos_iniciales': {'producto': 'Laptop', 'cantidad': 1, 'precio': 800.00},
                    'solucion_esperada': {'subtotal': 800.00, 'iva': 96.00, 'total': 896.00},
                    'dificultad': 1,
                    'puntos_max': 50
                },
                {
                    'nombre': 'Venta con Descuento',
                    'descripcion': 'Venta con descuento aplicado',
                    'datos_iniciales': {'producto': 'Mouse', 'cantidad': 2, 'precio': 25.00, 'descuento': 10},
                    'solucion_esperada': {'subtotal': 45.00, 'iva': 5.40, 'total': 50.40},
                    'dificultad': 2,
                    'puntos_max': 75
                }
            ]
        elif tipo.categoria == 'manufactura':
            escenarios = [
                {
                    'nombre': 'Producción Básica',
                    'descripcion': 'Orden de producción simple',
                    'datos_iniciales': {'producto': 'Mesa', 'cantidad': 5, 'material_costo': 50.00},
                    'solucion_esperada': {'costo_total': 250.00, 'costo_unitario': 50.00},
                    'dificultad': 1,
                    'puntos_max': 60
                }
            ]
        else:  # servicios
            escenarios = [
                {
                    'nombre': 'Consultoría Básica',
                    'descripcion': 'Facturación de horas de consultoría',
                    'datos_iniciales': {'servicio': 'Consultoría', 'horas': 4, 'tarifa': 50.00},
                    'solucion_esperada': {'subtotal': 200.00, 'iva': 24.00, 'total': 224.00},
                    'dificultad': 1,
                    'puntos_max': 45
                }
            ]
        
        for escenario_data in escenarios:
            escenario, created = EscenarioSimulacion.objects.get_or_create(
                tipo_simulacion=tipo,
                nombre=escenario_data['nombre'],
                defaults=escenario_data
            )
            if created:
                self.stdout.write(f'  [OK] Escenario: {escenario.nombre}')