"""API para manejo de códigos de barras"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from ..models import Producto
import logging

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def buscar_por_codigo_barras(request):
    """Busca producto por código de barras"""
    codigo = request.GET.get('codigo', '').strip()
    
    if not codigo:
        return JsonResponse({
            'encontrado': False,
            'error': 'Código requerido'
        })
    
    try:
        # Buscar por código de barras primero, luego por código interno
        producto = None
        
        # Intentar por código de barras
        if codigo:
            try:
                producto = Producto.objects.get(
                    codigo_barras=codigo,
                    empresa=request.user.empresa
                )
            except Producto.DoesNotExist:
                # Intentar por código interno como fallback
                try:
                    producto = Producto.objects.get(
                        codigo=codigo,
                        empresa=request.user.empresa
                    )
                except Producto.DoesNotExist:
                    pass
        
        if producto:
            logger.info(f"Producto encontrado por código: {codigo} - {producto.nombre}")
            return JsonResponse({
                'encontrado': True,
                'id': producto.id,
                'codigo': producto.codigo,
                'codigo_barras': producto.codigo_barras or '',
                'nombre': producto.nombre,
                'precio_unitario': str(producto.precio_unitario),
                'pvp': str(producto.pvp) if producto.pvp else '',
                'stock': producto.stock,
                'descripcion': producto.descripcion
            })
        else:
            logger.warning(f"Producto no encontrado para código: {codigo}")
            return JsonResponse({
                'encontrado': False,
                'mensaje': f'Producto con código "{codigo}" no encontrado'
            })
            
    except Exception as e:
        logger.error(f"Error buscando producto por código {codigo}: {str(e)}")
        return JsonResponse({
            'encontrado': False,
            'error': 'Error interno del servidor'
        })


@login_required
@require_http_methods(["GET"])
def validar_codigo_barras(request):
    """Valida formato de código de barras"""
    codigo = request.GET.get('codigo', '').strip()
    
    if not codigo:
        return JsonResponse({
            'valido': False,
            'error': 'Código requerido'
        })
    
    # Validaciones básicas de formato
    validaciones = {
        'longitud_valida': False,
        'solo_numeros': False,
        'formato_reconocido': False,
        'tipo_codigo': 'desconocido'
    }
    
    # Verificar que solo contenga números
    if codigo.isdigit():
        validaciones['solo_numeros'] = True
        
        # Verificar longitudes estándar
        if len(codigo) == 13:  # EAN-13
            validaciones['longitud_valida'] = True
            validaciones['formato_reconocido'] = True
            validaciones['tipo_codigo'] = 'EAN-13'
        elif len(codigo) == 12:  # UPC-A
            validaciones['longitud_valida'] = True
            validaciones['formato_reconocido'] = True
            validaciones['tipo_codigo'] = 'UPC-A'
        elif len(codigo) == 8:  # EAN-8
            validaciones['longitud_valida'] = True
            validaciones['formato_reconocido'] = True
            validaciones['tipo_codigo'] = 'EAN-8'
        elif 6 <= len(codigo) <= 20:  # Code 128 variable
            validaciones['longitud_valida'] = True
            validaciones['formato_reconocido'] = True
            validaciones['tipo_codigo'] = 'Code 128'
    
    es_valido = all([
        validaciones['solo_numeros'],
        validaciones['longitud_valida'],
        validaciones['formato_reconocido']
    ])
    
    return JsonResponse({
        'valido': es_valido,
        'tipo_codigo': validaciones['tipo_codigo'],
        'detalles': validaciones
    })

@login_required
def crear_categoria_api(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            nombre = data.get('nombre')
            descripcion = data.get('descripcion', '')
            
            if not nombre:
                return JsonResponse({'success': False, 'error': 'Nombre requerido'})
            
            from empresa.models import CategoriaProducto
            categoria = CategoriaProducto.objects.create(
                empresa=request.user.empresa,
                nombre=nombre,
                descripcion=descripcion
            )
            
            return JsonResponse({
                'success': True,
                'categoria': {
                    'id': categoria.id,
                    'nombre': categoria.nombre
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def materias_primas_api(request):
    """API para obtener materias primas de la empresa"""
    if request.method == 'GET':
        from empresa.models import MateriaPrima
        materias = MateriaPrima.objects.filter(empresa=request.user.empresa)
        
        data = []
        for materia in materias:
            data.append({
                'id': materia.id,
                'nombre': materia.nombre,
                'precio_unitario': str(materia.precio_unitario),
                'unidad_medida': materia.unidad_medida,
                'stock_actual': str(materia.stock_actual)
            })
        
        return JsonResponse(data, safe=False)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)