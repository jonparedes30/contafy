import json
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion

m, created = ModuloAprendizaje.objects.get_or_create(
    nombre='Demo Comercio',
    tipo_empresa='comercial',
    defaults={'descripcion':'Módulo demo generado automáticamente', 'orden': 1}
)

pasos = [
    {
        'titulo': '📦 Paso 1: Crear Producto',
        'descripcion': 'Crea un producto en Inventario',
        'accion': 'crear_producto',
        'datos': {'nombre': 'Camiseta Demo', 'codigo': 'CAM-DEMO', 'precio_venta': 15}
    },
    {
        'titulo': '💵 Paso 2: Registrar Venta',
        'descripcion': 'Registra una venta del producto creado',
        'accion': 'crear_venta',
        'datos': {'cantidad': 2, 'producto': 'Camiseta Demo'}
    }
]

# Intentar guardar pasos como lista (si JSONField) o como JSON string (si TextField)
try:
    le = Leccion.objects.create(
        modulo=m,
        titulo='Venta básica (Demo)',
        tipo='practica',
        contenido='Lección demo: registra una venta paso a paso.',
        puntos_xp=20,
        tiempo_estimado=5,
        orden=1,
        pasos=pasos
    )
except Exception:
    le = Leccion.objects.create(
        modulo=m,
        titulo='Venta básica (Demo)',
        tipo='practica',
        contenido='Lección demo: registra una venta paso a paso.',
        puntos_xp=20,
        tiempo_estimado=5,
        orden=1,
        pasos=json.dumps(pasos)
    )

print('Lección demo creada, id:', le.id)
