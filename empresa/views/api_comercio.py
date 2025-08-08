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
    empresa = request.user.empresa
    
    if request.method == 'GET':
        categorias = CategoriaProducto.objects.filter(empresa=empresa).values(
            'id', 'nombre', 'descripcion', 'activa'
        )
        return JsonResponse(list(categorias), safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            categoria = CategoriaProducto.objects.create(
                empresa=empresa,
                nombre=data['nombre'],
                descripcion=data.get('descripcion', ''),
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
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def categoria_delete_api(request, categoria_id):
    try:
        categoria = CategoriaProducto.objects.get(
            id=categoria_id, 
            empresa=request.user.empresa
        )
        categoria.delete()
        return JsonResponse({'success': True})
    except CategoriaProducto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Categoría no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def clientes_api(request):
    try:
        data = json.loads(request.body)
        cliente = Cliente.objects.create(
            empresa=request.user.empresa,
            nombre=data['nombre'],
            numero_documento=data.get('numero_documento', ''),
            telefono=data.get('telefono', ''),
            limite_credito=data.get('limite_credito', 0)
        )
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def proveedores_api(request):
    try:
        data = json.loads(request.body)
        proveedor = Proveedor.objects.create(
            empresa=request.user.empresa,
            nombre=data['nombre'],
            ruc=data.get('ruc', ''),
            telefono=data.get('telefono', ''),
            dias_credito=data.get('dias_credito', 0)
        )
        return JsonResponse({
            'success': True,
            'proveedor': {
                'id': proveedor.id,
                'nombre': proveedor.nombre
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def cuentas_cobrar_api(request):
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


@login_required
def cuentas_pagar_api(request):
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