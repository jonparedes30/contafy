"""APIs para funcionalidades de comercio"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
from datetime import date
from ..models import CategoriaProducto, Cliente, Proveedor, CuentaPorCobrar, CuentaPorPagar


@login_required
@require_http_methods(["GET", "POST"])
@csrf_exempt
def categorias_api(request):
    try:
        empresa = request.user.empresa
        
        if request.method == 'GET':
            categorias = CategoriaProducto.objects.filter(empresa=empresa).values(
                'id', 'nombre', 'descripcion', 'activa'
            )
            return JsonResponse(list(categorias), safe=False)
        
        elif request.method == 'POST':
            try:
                data = json.loads(request.body)
                
                # Validar que el nombre no esté vacío
                if not data.get('nombre', '').strip():
                    return JsonResponse({'success': False, 'error': 'El nombre es requerido'})
                
                # Verificar si ya existe una categoría con ese nombre
                if CategoriaProducto.objects.filter(empresa=empresa, nombre=data['nombre']).exists():
                    return JsonResponse({'success': False, 'error': 'Ya existe una categoría con ese nombre'})
                
                categoria = CategoriaProducto.objects.create(
                    empresa=empresa,
                    nombre=data['nombre'].strip(),
                    descripcion=data.get('descripcion', '').strip(),
                    activa=True
                )
                return JsonResponse({
                    'success': True,
                    'categoria': {
                        'id': categoria.id,
                        'nombre': categoria.nombre,
                        'descripcion': categoria.descripcion
                    }
                })
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error de autenticación: {str(e)}'})


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def categoria_delete_api(request, categoria_id):
    try:
        categoria = CategoriaProducto.objects.get(
            id=categoria_id, 
            empresa=request.user.empresa
        )
        
        # Verificar si hay productos usando esta categoría
        productos_count = categoria.producto_set.count()
        if productos_count > 0:
            return JsonResponse({
                'success': False, 
                'error': f'No se puede eliminar. Hay {productos_count} productos usando esta categoría'
            })
        
        categoria.delete()
        return JsonResponse({'success': True})
    except CategoriaProducto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Categoría no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error eliminando categoría: {str(e)}'})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def clientes_api(request):
    try:
        data = json.loads(request.body)
        
        # Validaciones
        if not data.get('nombre', '').strip():
            return JsonResponse({'success': False, 'error': 'El nombre es requerido'})
        
        cliente = Cliente.objects.create(
            empresa=request.user.empresa,
            nombre=data['nombre'].strip(),
            numero_documento=data.get('numero_documento', '').strip(),
            telefono=data.get('telefono', '').strip(),
            limite_credito=float(data.get('limite_credito', 0))
        )
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Valor numérico inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error creando cliente: {str(e)}'})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def proveedores_api(request):
    try:
        data = json.loads(request.body)
        
        # Validaciones
        if not data.get('nombre', '').strip():
            return JsonResponse({'success': False, 'error': 'El nombre es requerido'})
        
        proveedor = Proveedor.objects.create(
            empresa=request.user.empresa,
            nombre=data['nombre'].strip(),
            ruc=data.get('ruc', '').strip(),
            telefono=data.get('telefono', '').strip(),
            dias_credito=int(data.get('dias_credito', 0))
        )
        return JsonResponse({
            'success': True,
            'proveedor': {
                'id': proveedor.id,
                'nombre': proveedor.nombre
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Valor numérico inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error creando proveedor: {str(e)}'})


@login_required
def cuentas_cobrar_api(request):
    try:
        empresa = request.user.empresa
        cuentas = CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado='pendiente',
            monto_pendiente__gt=0
        ).select_related('cliente').order_by('fecha_vencimiento')
        
        data = []
        for cuenta in cuentas:
            dias_vencido = max(0, (date.today() - cuenta.fecha_vencimiento).days)
            data.append({
                'cliente_nombre': cuenta.cliente.nombre,
                'monto_pendiente': float(cuenta.monto_pendiente),
                'fecha_vencimiento': cuenta.fecha_vencimiento.strftime('%Y-%m-%d'),
                'dias_vencido': dias_vencido
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': f'Error obteniendo cuentas por cobrar: {str(e)}'}, status=500)


@login_required
def cuentas_pagar_api(request):
    try:
        empresa = request.user.empresa
        cuentas = CuentaPorPagar.objects.filter(
            empresa=empresa,
            estado='pendiente',
            monto_pendiente__gt=0
        ).select_related('proveedor').order_by('fecha_vencimiento')
        
        data = []
        for cuenta in cuentas:
            dias_vencido = max(0, (date.today() - cuenta.fecha_vencimiento).days)
            data.append({
                'proveedor_nombre': cuenta.proveedor.nombre,
                'monto_pendiente': float(cuenta.monto_pendiente),
                'fecha_vencimiento': cuenta.fecha_vencimiento.strftime('%Y-%m-%d'),
                'dias_vencido': dias_vencido
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': f'Error obteniendo cuentas por pagar: {str(e)}'}, status=500)