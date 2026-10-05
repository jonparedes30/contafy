# empresa/views/compras.py
from empresa.utils.errores import mensaje_error
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from empresa.models import Compra, Producto
from empresa.forms import CompraForm
from empresa.views.contabilidad import registrar_movimiento_contable
from empresa.decorators import require_power
from django.db import transaction
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q
from decimal import Decimal

@login_required
@require_power('puede_registrar_compras')
def crear_compra(request):
    empresa = request.user.empresa

    if request.method == 'POST':
        # If JSON payload (scanner integration) -> allow prefill or direct create
        if request.content_type and 'application/json' in request.content_type:
            try:
                payload = json.loads(request.body.decode('utf-8'))
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'JSON inválido: {e}'}, status=400)

            # Prefill request: barcode or detection provided
            if payload.get('barcode') or payload.get('detection'):
                barcode = payload.get('barcode')
                detection = payload.get('detection') or {}
                # search product only within empresa
                if barcode:
                    prod = Producto.objects.filter(empresa=empresa, codigo_barras=barcode).first()
                    if prod:
                        return JsonResponse({'success': True, 'found': True, 'product': {
                            'id': prod.id,
                            'nombre': prod.nombre,
                            'stock': prod.stock,
                            'precio_unitario': float(prod.precio_unitario) if prod.precio_unitario is not None else None,
                            'codigo_barras': prod.codigo_barras
                        }})
                # try ocr/text match
                candidate = None
                ocr_texts = detection.get('ocr') if isinstance(detection, dict) else []
                if ocr_texts:
                    candidate = ocr_texts[0]
                if not barcode and detection.get('logos'):
                    candidate = candidate or (detection.get('logos')[0] if detection.get('logos') else None)
                if candidate:
                    prod = Producto.objects.filter(empresa=empresa, nombre__icontains=candidate).first()
                    if prod:
                        return JsonResponse({'success': True, 'found': True, 'product': {
                            'id': prod.id,
                            'nombre': prod.nombre,
                            'stock': prod.stock,
                            'precio_unitario': float(prod.precio_unitario) if prod.precio_unitario is not None else None,
                            'codigo_barras': prod.codigo_barras
                        }})

                return JsonResponse({'success': True, 'found': False, 'message': 'Producto no registrado en inventario'})

            # Direct create compra via JSON (e.g., frontend posts compra data)
            if payload.get('producto_id') and payload.get('cantidad'):
                try:
                    producto = Producto.objects.select_for_update().get(id=int(payload.get('producto_id')), empresa=empresa)
                except Producto.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Producto no encontrado en inventario'}, status=404)

                cantidad = int(payload.get('cantidad'))
                precio_unitario = float(payload.get('precio_unitario') or producto.precio_unitario or 0)
                tipo_pago = payload.get('tipo_pago', 'contado')
                cliente = payload.get('proveedor', '')

                if cantidad <= 0:
                    return JsonResponse({'success': False, 'error': 'Cantidad inválida'}, status=400)

                try:
                    with transaction.atomic():
                        compra = Compra(
                            empresa=empresa,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            monto=cantidad * precio_unitario,
                            tipo_pago=tipo_pago,
                            creado_por=request.user
                        )
                        compra.save()
                        producto.stock += cantidad
                        producto.save()
                        # registrar movimiento contable
                        if compra.tipo_pago == 'contado':
                            cuenta_credito = 'Caja/Banco'
                        else:
                            cuenta_credito = 'Cuentas por Pagar'
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Inventario',
                            cuenta_credito_nombre=cuenta_credito,
                            monto=compra.monto,
                            descripcion=f"Compra de {producto.nombre} (x{compra.cantidad}) - {compra.get_tipo_pago_display()}",
                            tipo_cuenta_debito='activo',
                            tipo_cuenta_credito='activo' if compra.tipo_pago == 'contado' else 'pasivo'
                        )
                    return JsonResponse({'success': True, 'compra_id': compra.id, 'product': {'id': producto.id, 'stock': producto.stock, 'nombre': producto.nombre}})
                except Exception as e:
                    return JsonResponse({'success': False, 'error': mensaje_error(e)}, status=500)

            return JsonResponse({'success': False, 'error': 'Payload JSON no reconocido'}, status=400)

        # end JSON handling
        form = CompraForm(request.POST, empresa=empresa)
        if form.is_valid():
            try:
                with transaction.atomic():
                    compra = form.save(commit=False)
                    compra.empresa = empresa
                    compra.creado_por = request.user
                    compra.save()  # El modelo se encarga automáticamente de crear la cuenta por pagar
                    
                    # Actualizar stock del producto
                    producto = compra.producto
                    producto.stock += compra.cantidad
                    producto.save()
                    # Registrar compra según tipo de pago
                    if compra.tipo_pago == 'contado':
                        cuenta_credito = 'Caja/Banco'
                    else:
                        cuenta_credito = 'Cuentas por Pagar'
                    
                    registrar_movimiento_contable(
                        empresa=empresa,
                        cuenta_debito_nombre='Inventario',
                        cuenta_credito_nombre=cuenta_credito,
                        monto=compra.monto,
                        descripcion=f"Compra de {compra.producto.nombre} (x{compra.cantidad}) - {compra.get_tipo_pago_display()}",
                        tipo_cuenta_debito='activo',
                        tipo_cuenta_credito='activo' if compra.tipo_pago == 'contado' else 'pasivo'
                    )
                messages.success(request, 'Compra registrada correctamente.')
                return redirect('empresa:home')
            except Exception as e:
                messages.error(request, f'Error al registrar compra: {e}')
    else:
        form = CompraForm(empresa=empresa)

    # Preparar JSON de productos para el JS
    productos = Producto.objects.filter(empresa=empresa).values(
        'id', 'codigo', 'codigo_barras', 'nombre', 'precio_unitario', 'stock'
    )
    # Helper para convertir Decimals a float
    from decimal import Decimal
    def decimal_to_float(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, dict):
            return {k: decimal_to_float(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [decimal_to_float(i) for i in obj]
        return obj
    productos_list = []
    for p in productos:
        productos_list.append({
            'id': p['id'],
            'codigo': p['codigo'],
            'codigo_barras': p['codigo_barras'] or '',
            'nombre': p['nombre'],
            'precio_unitario': float(p['precio_unitario']),
            'stock': p['stock']
        })
    productos_json = json.dumps(productos_list)

    return render(request, 'empresa/crear_compra.html', {
        'form': form,
        'productos_json': productos_json,
    })


@login_required
@require_power('puede_registrar_compras')
def listar_compras(request):
    empresa = request.user.empresa
    compras = Compra.objects.filter(empresa=empresa).order_by('-fecha')

    # Filtros avanzados
    buscar = request.GET.get('buscar', '').strip()
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    monto = request.GET.get('monto')

    if buscar:
        compras = compras.filter(
            Q(producto__nombre__icontains=buscar) |
            Q(producto__codigo__icontains=buscar) |
            Q(proveedor__icontains=buscar)
        )
    if fecha_desde:
        compras = compras.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        compras = compras.filter(fecha__date__lte=fecha_hasta)
    if monto:
        if '-' in monto:
            min_monto, max_monto = monto.split('-')
            compras = compras.filter(monto__gte=float(min_monto), monto__lte=float(max_monto))
        elif monto.endswith('+'):
            min_monto = monto.replace('+', '')
            compras = compras.filter(monto__gte=float(min_monto))

    # Estadísticas generales
    total_compras = compras.aggregate(total=Sum('monto'))['total'] or 0
    total_transacciones = compras.count()
    promedio_compra = compras.aggregate(promedio=Avg('monto'))['promedio'] or 0
    
    es_propietario = not hasattr(request.user, 'poderes') or request.user.is_superuser

    # Paginación: 15 registros por página
    paginator = Paginator(compras, 15)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    contexto = {
        'page_obj': page_obj,
        'compras': page_obj.object_list,
        'total_compras': total_compras,
        'total_transacciones': total_transacciones,
        'promedio_compra': promedio_compra,
        'es_propietario': es_propietario,
    }
    return render(request, 'empresa/listar_compra.html', contexto)

@login_required
@require_power('puede_editar_compras')
def editar_compra(request, compra_id):
    from django.shortcuts import get_object_or_404
    
    if hasattr(request.user, 'poderes') and not request.user.is_superuser:
        messages.error(request, 'Solo el propietario puede editar compras.')
        return redirect('empresa:listar_compras')
    
    empresa = request.user.empresa
    compra = get_object_or_404(Compra, id=compra_id, empresa=empresa)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                compra.producto.stock -= compra.cantidad
                
                compra.cantidad = int(request.POST.get('cantidad', compra.cantidad))
                monto_raw = request.POST.get('monto', None)
                if monto_raw is not None:
                    compra.monto = Decimal(str(monto_raw))
                else:
                    compra.monto = Decimal(compra.monto)
                
                compra.producto.stock += compra.cantidad
                compra.producto.save()
                compra.save()
                
                messages.success(request, 'Compra actualizada correctamente.')
                return redirect('empresa:listar_compras')
        except Exception as e:
            messages.error(request, f'Error al actualizar compra: {str(e)}')
    
    context = {'compra': compra}
    return render(request, 'empresa/editar_compra.html', context)

@login_required
@require_power('puede_eliminar_compras')
def eliminar_compra(request, compra_id):
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    
    if hasattr(request.user, 'poderes') and not request.user.is_superuser:
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if request.method == 'POST':
        try:
            empresa = request.user.empresa
            compra = get_object_or_404(Compra, id=compra_id, empresa=empresa)
            
            producto = compra.producto
            producto.stock -= compra.cantidad
            producto.save()
            
            compra.delete()
            
            messages.success(request, 'Compra eliminada correctamente.')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': mensaje_error(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============================================================================
# ESCÁNER VISION - API UNIFICADA para Inventario, Compras y Ventas
# ============================================================================
from django.http import JsonResponse
import requests
from django.conf import settings
import time
import re
import traceback
import base64
import logging

logger = logging.getLogger(__name__)


@login_required
def vision_search_api(request):
    """
    API única del escáner para Ventas (POS), Compras e Inventario.

    Entrada JSON (una de las dos):
        {"codigo": "7861234567890", "contexto": "venta"}        # código leído por cámara/lector
        {"image": "data:image/jpeg;base64,...", "contexto": "compra"}  # foto -> Google Vision

    Salida: ver empresa.services.escaner_service.identificar().
    """
    from empresa.services.escaner_service import EscanerError, identificar

    if request.method != 'POST':
        return JsonResponse({'success': False, 'ok': False, 'error': 'Solo se permite método POST'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': 'Solicitud inválida'}, status=400)

    contexto = data.get('contexto', 'compra')
    codigo = str(data.get('codigo') or '').strip()[:50]
    imagen = data.get('image') or ''
    if 'base64,' in imagen:
        imagen = imagen.split('base64,', 1)[1]
    if imagen and not codigo:
        try:
            tamano_mb = len(base64.b64decode(imagen, validate=False)) / (1024 * 1024)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'La imagen no es válida.'}, status=400)
        if tamano_mb < 0.01 or tamano_mb > 10:
            return JsonResponse({'success': False, 'error': 'La foto debe pesar entre 10 KB y 10 MB.'}, status=400)

    inicio = time.time()
    try:
        respuesta = identificar(request.user.empresa, contexto=contexto, codigo=codigo, imagen_b64=imagen)
    except EscanerError as e:
        return JsonResponse({'success': False, 'ok': False, 'error': str(e), 'productos': [], 'products': []})
    except Exception:
        logger.exception('Error inesperado en vision_search_api')
        return JsonResponse({'success': False, 'ok': False, 'error': 'No se pudo identificar el producto.',
                             'productos': [], 'products': []}, status=500)

    logger.info('vision_search_api: %s productos por %s en %.2fs (contexto=%s)',
                respuesta['meta']['total'], respuesta['origen'], time.time() - inicio, contexto)
    return JsonResponse(respuesta)
