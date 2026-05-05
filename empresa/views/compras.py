# empresa/views/compras.py
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from empresa.models import Compra, Producto
from empresa.forms import CompraForm
from empresa.views.contabilidad import registrar_movimiento_contable
from django.db import transaction
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q
from decimal import Decimal

@login_required
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
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============================================================================
# ESCÁNER VISION - API UNIFICADA para Inventario, Compras y Ventas
# ============================================================================
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from django.conf import settings
import time
import re
import traceback
import base64
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
def vision_search_api(request):
    """
    API Unificada de Escáner para Inventario, Compras y Ventas.

    Entrada JSON:
    {
        "image": "data:image/jpeg;base64,...",
        "contexto": "inventario" | "compra" | "venta"
    }

    Salida JSON:
    {
        "success": True,
        "ok": True,
        "found": True/False,
        "productos": [...],
        "products": [...],
        "codigo_detectado": "...",
        "meta": {...},
        "debug": {...}
    }
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'ok': False,
            'error': 'Solo se permite método POST'
        }, status=405)

    inicio = time.time()
    empresa = request.user.empresa

    try:
        data = json.loads(request.body.decode('utf-8'))
        image_data = data.get('image', '')
        contexto = data.get('contexto', 'compra')

        if not image_data:
            return JsonResponse({
                'success': False,
                'error': 'Falta el campo "image" en la solicitud'
            }, status=400)

        if 'base64,' in image_data:
            image_data = image_data.split('base64,', 1)[1]

        try:
            decoded_image = base64.b64decode(image_data)
            image_size_mb = len(decoded_image) / (1024 * 1024)

            if image_size_mb < 0.01:
                return JsonResponse({
                    'success': False,
                    'error': 'La imagen es demasiado pequeña (mínimo 10 KB)'
                }, status=400)

            if image_size_mb > 10:
                return JsonResponse({
                    'success': False,
                    'error': 'La imagen es demasiado grande (máximo 10 MB)'
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al decodificar la imagen: {str(e)}'
            }, status=400)

        api_key = getattr(settings, 'GOOGLE_VISION_API_KEY', None)
        if not api_key:
            return JsonResponse({
                'success': False,
                'error': 'GOOGLE_VISION_API_KEY no configurada en settings.py'
            }, status=500)

        vision_url = f'https://vision.googleapis.com/v1/images:annotate?key={api_key}'
        payload = {
            'requests': [{
                'image': {'content': image_data},
                'features': [
                    {'type': 'LOGO_DETECTION', 'maxResults': 5},
                    {'type': 'TEXT_DETECTION', 'maxResults': 1},
                    {'type': 'LABEL_DETECTION', 'maxResults': 5}
                ]
            }]
        }

        try:
            vision_response = requests.post(vision_url, json=payload, timeout=10)
            vision_response.raise_for_status()
            vision_data = vision_response.json()
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al llamar a Google Vision API: {str(e)}'
            }, status=500)

        responses = vision_data.get('responses', [])
        if not responses:
            return JsonResponse({
                'success': False,
                'error': 'Google Vision no devolvió respuestas'
            }, status=500)

        response = responses[0]

        logos = []
        for annotation in response.get('logoAnnotations', []):
            logo_name = annotation.get('description', '')
            if logo_name:
                logos.append(logo_name)

        full_text_ann = response.get('fullTextAnnotation') or {}
        texto_completo = full_text_ann.get('text', '') if isinstance(full_text_ann, dict) else ''
        if not texto_completo and response.get('textAnnotations'):
            texto_completo = response['textAnnotations'][0].get('description', '')

        labels = []
        for label in response.get('labelAnnotations', []):
            label_name = label.get('description', '')
            if label_name:
                labels.append(label_name)

        palabras_blacklist = [
            'peso', 'neto', 'ingredientes', 'tabla', 'nutricional', 'información',
            'calorías', 'proteínas', 'grasas', 'carbohidratos', 'sodio',
            'contiene', 'elaborado', 'conservar', 'fecha', 'lote', 'reg',
            'sanitario', 'hecho', 'producto', 'alimento', 'natural', 'artificial',
            'cont', 'grasa', 'azucar', 'exceso', 'min', 'max', 'valor', 'total', 'precio',
            'g', 'kg', 'ml', 'l', 'oz', 'lb', 'exp', 'pvp'
        ]

        lines = texto_completo.split('\n')
        lineas_limpias = []

        for linea in lines[:10]:
            linea = linea.strip()
            if len(linea) < 3:
                continue
            es_ruido = any(palabra in linea.lower() for palabra in palabras_blacklist)
            if es_ruido:
                continue
            lineas_limpias.append(linea)

        codigo_detectado = None
        patron_codigo = r'\b\d{8,14}\b'
        for linea in lines:
            match = re.search(patron_codigo, linea)
            if match:
                codigo_detectado = match.group()
                break

        query = Q()

        if codigo_detectado:
            query |= Q(codigo_barras__exact=codigo_detectado)
            query |= Q(codigo__exact=codigo_detectado)
            query |= Q(codigo_barras__icontains=codigo_detectado)
            query |= Q(codigo__icontains=codigo_detectado)

        for logo in logos:
            if len(logo) >= 3:
                query |= Q(nombre__icontains=logo)

        for linea in lineas_limpias[:3]:
            if len(linea) >= 3:
                query |= Q(nombre__icontains=linea)

        productos_qs = Producto.objects.filter(empresa=empresa)

        if contexto == 'venta':
            productos_qs = productos_qs.filter(stock__gt=0)

        if query:
            productos_qs = productos_qs.filter(query).distinct()[:5]
        else:
            productos_qs = productos_qs.none()

        productos_list = []

        for producto in productos_qs:
            item = {
                'id': producto.id,
                'nombre': producto.nombre,
                'codigo': producto.codigo or '',
                'codigo_barras': producto.codigo_barras or '',
                'stock': producto.stock,
            }

            if hasattr(producto, 'categoria') and producto.categoria:
                item['categoria'] = producto.categoria.nombre
            else:
                item['categoria'] = ''

            if contexto == 'compra':
                item['precio_unitario'] = float(producto.precio_unitario or 0)
                item['ultimo_costo'] = float(producto.precio_unitario or 0)
                item['pvp'] = float(producto.pvp or 0)
                item['stock_minimo'] = getattr(producto, 'stock_minimo', 0) or 0

            elif contexto == 'venta':
                item['pvp'] = float(producto.pvp or 0)
                item['precio_venta'] = float(producto.pvp or producto.precio_unitario or 0)
                item['precio'] = float(producto.pvp or producto.precio_unitario or 0)
                item['stock_disponible'] = producto.stock

            elif contexto == 'inventario':
                item['precio_unitario'] = float(producto.precio_unitario or 0)
                item['pvp'] = float(producto.pvp or 0)
                item['activo'] = getattr(producto, 'activo', True)

            productos_list.append(item)

        tiempo_total = time.time() - inicio
        logger.info(f'vision_search_api: {len(productos_list)} productos en {tiempo_total:.2f}s (contexto={contexto})')

        response_data = {
            'success': True,
            'ok': True,
            'found': len(productos_list) > 0,
            'productos': productos_list,
            'products': productos_list,
            'codigo_detectado': codigo_detectado or '',
            'meta': {
                'total': len(productos_list),
                'contexto': contexto,
                'api_version': '2.0'
            },
            'debug': {
                'logos': logos,
                'textos': lineas_limpias[:5],
                'labels': labels[:5],
                'texto_completo': texto_completo[:200],
                'search_terms': lineas_limpias[:3] + logos[:2]
            }
        }

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido en el cuerpo de la solicitud'
        }, status=400)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f'Error en vision_search_api: {error_msg}', exc_info=True)
        return JsonResponse({
            'success': False,
            'ok': False,
            'error': f'Error interno del servidor: {str(e)}',
            'traceback': error_trace if getattr(settings, 'DEBUG', False) else None,
            'productos': [],
            'products': []
        }, status=500)

