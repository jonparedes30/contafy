from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.db.models import F
from django.db.models.functions import Greatest
from django.contrib import messages
from empresa.models import Producto
from empresa.forms import ProductoForm
from empresa.decorators import require_power
from django.contrib import messages
import requests
import json
import uuid
import traceback
import logging

logger = logging.getLogger(__name__)

# Intentar importar TrigramSimilarity (solo disponible en PostgreSQL)
try:
    from django.contrib.postgres.search import TrigramSimilarity
    HAS_TRIGRAM = True
except ImportError:
    HAS_TRIGRAM = False
    TrigramSimilarity = None


@login_required
@require_power('puede_editar_productos')
def crear_producto(request):
    empresa = request.user.empresa

    if request.method == 'POST':
        # Support JSON POST (scanner integration) as well as form POST
        if request.content_type and 'application/json' in request.content_type:
            try:
                payload = json.loads(request.body.decode('utf-8'))
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'JSON inválido: {e}'}, status=400)

            # Extract fields from payload
            nombre = payload.get('nombre') or payload.get('detection', {}).get('nombre') or payload.get('marca')
            descripcion = payload.get('presentacion') or payload.get('descripcion') or ''
            codigo_barras = payload.get('barcode') or payload.get('codigo_barras') or None
            stock = int(payload.get('stock') or 0)
            precio = payload.get('precio_unitario') or payload.get('precio') or 0

            from django.db import transaction
            from empresa.views.contabilidad import registrar_movimiento_contable
            try:
                with transaction.atomic():
                    # create product
                    producto = Producto.objects.create(
                        empresa=empresa,
                        codigo=payload.get('codigo') or f"SCAN-{uuid.uuid4().hex[:8]}",
                        codigo_barras=codigo_barras,
                        nombre=nombre or 'Producto escaneado',
                        descripcion=descripcion,
                        precio_unitario=precio,
                        pvp=precio,
                        stock=stock
                    )

                    # register initial inventory if stock
                    if producto.stock > 0 and producto.precio_unitario > 0:
                        costo_total = producto.stock * producto.precio_unitario
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Inventario',
                            cuenta_credito_nombre='Capital',
                            monto=costo_total,
                            descripcion=f"Inventario inicial: {producto.nombre} (x{producto.stock})",
                            tipo_cuenta_debito='activo',
                            tipo_cuenta_credito='capital'
                        )

                return JsonResponse({'success': True, 'product': {
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'stock': producto.stock,
                    'precio_unitario': float(producto.precio_unitario) if producto.precio_unitario is not None else None,
                    'codigo_barras': producto.codigo_barras
                }})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)

        else:
            form = ProductoForm(request.POST, empresa=empresa)
            if form.is_valid():
                from django.db import transaction
                from empresa.views.contabilidad import registrar_movimiento_contable
                
                try:
                    with transaction.atomic():
                        producto = form.save()
                        
                        # REGISTRAR COMPRA INICIAL SI HAY STOCK
                        if producto.stock > 0 and producto.precio_unitario > 0:
                            costo_total = producto.stock * producto.precio_unitario
                            
                            # Registrar movimiento contable: Débito Inventario + Crédito Capital
                            registrar_movimiento_contable(
                                empresa=empresa,
                                cuenta_debito_nombre='Inventario',
                                cuenta_credito_nombre='Capital',
                                monto=costo_total,
                                descripcion=f"Inventario inicial: {producto.nombre} (x{producto.stock})",
                                tipo_cuenta_debito='activo',
                                tipo_cuenta_credito='capital'
                            )
                            
                            messages.success(request, f'Producto creado e inventario inicial registrado: ${costo_total:,.2f}')
                        else:
                            messages.success(request, 'Producto creado correctamente')
                            
                except Exception as e:
                    messages.error(request, f'Error creando producto: {e}')
                    return render(request, 'empresa/crear_producto.html', {'form': form})
                    
                return redirect('empresa:home')
    else:
        form = ProductoForm(empresa=empresa)

    return render(request, 'empresa/crear_producto.html', {'form': form})


@login_required
@require_power('puede_gestionar_inventario')
def listar_productos(request):
    empresa = request.user.empresa
    
    # Obtener parámetros de filtro
    buscar = request.GET.get('buscar', '')
    stock_filter = request.GET.get('stock', '')
    categoria_filter = request.GET.get('categoria', '')
    
    # Filtrar productos
    productos = Producto.objects.filter(empresa=empresa)
    
    if buscar:
        productos = productos.filter(
            Q(codigo__icontains=buscar) |
            Q(nombre__icontains=buscar) |
            Q(descripcion__icontains=buscar) |
            Q(codigo_barras__icontains=buscar)
        )
    
    if stock_filter:
        if stock_filter == 'alto':
            productos = productos.filter(stock__gt=20)
        elif stock_filter == 'medio':
            productos = productos.filter(stock__gt=10, stock__lte=20)
        elif stock_filter == 'bajo':
            productos = productos.filter(stock__gt=0, stock__lte=10)
        elif stock_filter == 'agotado':
            productos = productos.filter(stock=0)
    
    if categoria_filter:
        productos = productos.filter(categoria_id=categoria_filter)
    
    # Ordenar por nombre
    productos = productos.order_by('nombre')
    
    # Obtener categorías para el filtro
    from empresa.models import CategoriaProducto
    categorias = CategoriaProducto.objects.filter(empresa=empresa, activa=True).order_by('nombre')
    
    # Calcular estadísticas (usar Decimal para evitar errores de precisión)
    from empresa.utils.money import to_decimal, quantize_currency
    total_inventario = sum((to_decimal(p.stock) * to_decimal(p.precio_unitario)) for p in productos)
    total_inventario = quantize_currency(total_inventario)
    total_pvp = sum((to_decimal(p.stock) * to_decimal(p.pvp or 0)) for p in productos)
    total_pvp = quantize_currency(total_pvp)
    productos_bajo_stock = productos.filter(stock__lte=10).count()
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'total_inventario': total_inventario,
        'total_pvp': total_pvp,
        'productos_bajo_stock': productos_bajo_stock,
    }
    
    return render(request, 'empresa/listar_productos_final.html', context)


@login_required
def obtener_info_producto(request):
    # Esta función puede quedar como compatibilidad, pero la búsqueda principal es en info_producto_api
    return JsonResponse({'error': 'Usa el endpoint principal de info_producto_api'}, status=404)


@login_required
def info_producto_api(request):
    codigo = request.GET.get('codigo', '')
    empresa = request.user.empresa
    
    # 1. Consultar API global (Open Food Facts)
    api_url = f'https://world.openfoodfacts.org/api/v0/product/{codigo}.json'
    try:
        # En modo sandbox evitamos consultas externas y devolvemos None para
        # que la b\u00fasqueda local se ejecute. Esto previene llamadas a servicios
        # externos durante simulaciones.
        from empresa.sandbox_mode import is_sandbox
        if is_sandbox():
            # Simular no encontrado en API externa cuando est\u00e1 en sandbox
            raise RuntimeError('Sandbox mode - skipping external API call')

        r = requests.get(api_url, timeout=4)
        if r.status_code == 200:
            data = r.json()
            if data.get('status') == 1:
                producto = data['product']
                nombre = producto.get('product_name', '')
                descripcion = producto.get('generic_name', '')
                if not descripcion:
                    descripcion = producto.get('categories', '')
                if not descripcion:
                    descripcion = producto.get('brands', '')
                if not descripcion:
                    descripcion = f"Producto: {nombre}"
                precio = ''
                return JsonResponse({
                    'nombre': nombre,
                    'descripcion': descripcion,
                    'categoria': producto.get('categories', '').split(',')[0] if producto.get('categories') else '',
                    'precio_unitario': precio,
                    'mensaje_precio': 'No se encontr\u00f3 precio autom\u00e1tico. Por favor, ingr\u00e9salo en USD.',
                    'fuente': 'api_global',
                })
    except Exception:
        # Silenciar errores y permitir la b\u00fasqueda local
        pass
    
    # 2. Si no se encuentra, buscar localmente SOLO en la empresa del usuario
    producto = Producto.objects.filter(codigo=codigo, empresa=empresa).first()
    if producto:
        return JsonResponse({
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'categoria': 'General',
            'precio_unitario': float(producto.precio_unitario),
            'mensaje_precio': '',
            'fuente': 'local',
        })
    
    # 3. No encontrado
    return JsonResponse({'error': 'No encontrado'}, status=404)


@login_required
@require_power('puede_editar_productos')
def editar_producto(request, producto_id):
    empresa = request.user.empresa
    try:
        producto = Producto.objects.get(id=producto_id, empresa=empresa)
    except Producto.DoesNotExist:
        messages.error(request, 'Producto no encontrado o no pertenece a tu empresa.')
        return redirect('empresa:listar_productos')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, empresa=empresa, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('empresa:home')
    else:
        form = ProductoForm(empresa=empresa, instance=producto)
    
    return render(request, 'empresa/crear_producto.html', {'form': form, 'producto': producto})


@login_required
def producto_info_api(request):
    """API endpoint para obtener información de producto por código o código de barras"""
    codigo = request.GET.get('codigo', '').strip()
    
    if not codigo:
        return JsonResponse({'error': 'Código requerido'}, status=400)
    
    empresa = request.user.empresa
    
    try:
        # Buscar por código o código de barras
        producto = Producto.objects.filter(
            empresa=empresa
        ).filter(
            Q(codigo=codigo) | Q(codigo_barras=codigo)
        ).first()
        
        if producto:
            return JsonResponse({
                'id': producto.id,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion or '',
                'codigo': producto.codigo,
                'codigo_barras': producto.codigo_barras or '',
                'precio_unitario': float(producto.precio_unitario) if producto.precio_unitario else 0,
                'stock': producto.stock,
                'fuente': 'local',
                'encontrado': True
            })
        else:
            # Aquí podrías agregar búsqueda en API global si existe
            return JsonResponse({
                'encontrado': False,
                'nombre': '',
                'descripcion': '',
                'precio_unitario': 0
            })
    except Exception as e:
        tb = traceback.format_exc()
        return JsonResponse({'error': str(e), 'traceback': tb}, status=500)


@login_required
def prefill_producto_from_scan(request):
    """
    Buscar producto en inventario por escaneo de visión o datos.

    FLUJO: vision_recognize -> envía detection -> este endpoint ->
    RESPONDE con matches (si encontró) o prefill (si no encontró)

    JSON POST: {"detection": {...}, o "nombre": "...", "marca": "..."}

    RESPUESTA SI ENCONTRÓ:
    {"found": true, "matches": [...], "mensaje": "..."}

    RESPUESTA SI NO ENCONTRÓ:
    {"found": false, "matches": [], "prefill": {...}}
    """
    # 1) Validar método HTTP
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # 2) Parsear JSON defensivamente
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
        logger.warning(f'JSON inválido en prefill_from_scan: {str(e)[:100]}')
        return JsonResponse({
            'error': 'JSON inválido',
            'encontrado': False,
            'matches': [],
            'sugerencia': None
        }, status=400)

    # Validar que sea dict
    if not isinstance(payload, dict):
        logger.warning(f'Payload no es dict: {type(payload)}')
        return JsonResponse({
            'error': 'Payload debe ser JSON object',
            'encontrado': False,
            'matches': [],
            'sugerencia': None
        }, status=400)

    # 3) Obtener empresa del usuario
    try:
        empresa = request.user.empresa
        if not empresa:
            logger.error(f'Usuario {request.user.id} sin empresa')
            return JsonResponse({
                'error': 'Usuario sin empresa asignada',
                'encontrado': False
            }, status=403)
    except Exception as e:
        logger.error(f'Error accediendo a empresa: {str(e)[:100]}')
        return JsonResponse({
            'error': 'Error de autenticación',
            'encontrado': False
        }, status=500)

    # 4) Extraer campos defensivamente (nunca asumir estructura)
    barcode = None
    try:
        barcode = str(payload.get('barcode') or payload.get('codigo_barras') or '').strip()
        if not barcode:
            barcode = None
    except (ValueError, TypeError):
        barcode = None

    nombre = None
    try:
        nombre = str(payload.get('nombre') or payload.get('marca') or '').strip()
        if not nombre:
            nombre = None
    except (ValueError, TypeError):
        nombre = None

    descripcion = None
    try:
        descripcion = str(payload.get('presentacion') or payload.get('descripcion') or '').strip()
        if not descripcion:
            descripcion = None
    except (ValueError, TypeError):
        descripcion = None

    codigo = None
    try:
        codigo = str(payload.get('codigo') or '').strip()
        if not codigo:
            codigo = None
    except (ValueError, TypeError):
        codigo = None

    precio = None
    try:
        precio = float(payload.get('precio_unitario') or payload.get('precio') or 0)
    except (ValueError, TypeError):
        precio = 0

    # --- FUNCIÓN HELPER PARA SERIALIZAR PRODUCTO ---
    def serialize_producto(producto):
        """Convierte Producto a dict seguro"""
        try:
            return {
                'id': producto.id,
                'nombre': str(producto.nombre or ''),
                'descripcion': str(producto.descripcion or ''),
                'codigo': str(producto.codigo or ''),
                'codigo_barras': str(producto.codigo_barras or ''),
                'precio_unitario': float(producto.precio_unitario or 0),
                'stock': int(producto.stock or 0),
                'encontrado': True,
                'fuente': 'local'
            }
        except Exception as e:
            logger.error(f'Error serializando producto {producto.id}: {str(e)[:100]}')
            return None

    def build_suggestion(producto=None):
        """Retorna sugerencia de prellenado vacío o del producto encontrado"""
        if producto:
            return serialize_producto(producto)

        # No encontrado: devolver estructura vacía pero válida
        return {
            'encontrado': False,
            'nombre': nombre or '',
            'descripcion': descripcion or '',
            'codigo_barras': barcode or '',
            'precio_unitario': precio or 0,
            'fuente': 'sugerido'
        }

    try:
        # --- ESTRATEGIA 1: Búsqueda exacta por barcode/código ---
        if barcode:
            try:
                producto = Producto.objects.filter(empresa=empresa).filter(
                    Q(codigo_barras__iexact=barcode) | Q(codigo__iexact=barcode)
                ).first()
                if producto:
                    logger.info(f'Encontrado por barcode: {producto.id}')
                    return JsonResponse(serialize_producto(producto))
            except Exception as e:
                logger.warning(f'Error en búsqueda por barcode: {str(e)[:100]}')

        if codigo:
            try:
                producto = Producto.objects.filter(empresa=empresa, codigo=codigo).first()
                if producto:
                    logger.info(f'Encontrado por código: {producto.id}')
                    return JsonResponse(serialize_producto(producto))
            except Exception as e:
                logger.warning(f'Error en búsqueda por código: {str(e)[:100]}')

        # --- ESTRATEGIA 2: Búsqueda fuzzy con probes (si array está disponible) ---
        probes = payload.get('probes')
        matches_map = {}

        # Normalizar probes
        probes_clean = []
        if probes:
            # Handle tanto string como list
            if isinstance(probes, str):
                probes = [probes]
            elif not isinstance(probes, list):
                probes = []

            for p in probes:
                try:
                    s = str(p or '').strip()
                    if len(s) > 2 and s not in probes_clean:  # Evitar searches muy cortos
                        probes_clean.append(s)
                except (ValueError, TypeError):
                    continue

            # Limitar a 5 probes para evitar queries pesadas
            probes_clean = probes_clean[:5]

        if probes_clean:
            try:
                # Intentar primero con TrigramSimilarity (PostgreSQL) si está disponible
                if HAS_TRIGRAM:
                    SIM_THRESHOLD = 0.25  # threshold bajo para ser permisivo

                    for probe in probes_clean:
                        try:
                            qs = Producto.objects.filter(empresa=empresa).annotate(
                                sim_nombre=TrigramSimilarity('nombre', probe),
                                sim_desc=TrigramSimilarity('descripcion', probe),
                            ).annotate(sim=Greatest(F('sim_nombre'), F('sim_desc'))).filter(
                                sim__gte=SIM_THRESHOLD
                            ).order_by('-sim')[:15]

                            for prod in qs:
                                score = float(getattr(prod, 'sim', 0.0) or 0.0)
                                cur = matches_map.get(prod.id)
                                if not cur or score > cur['score']:
                                    serialized = serialize_producto(prod)
                                    if serialized:
                                        serialized['score'] = score
                                        matches_map[prod.id] = serialized
                        except Exception as probe_err:
                            logger.warning(f'Error procesando probe "{probe}": {str(probe_err)[:100]}')
                            continue

                else:
                    # PostgreSQL no disponible, usar fallback directamente
                    raise Exception('TrigramSimilarity no disponible')

            except Exception as trigram_err:
                logger.info(f'TrigramSimilarity no disponible ({str(trigram_err)[:50]}), usando icontains')

                # --- FALLBACK: búsqueda simple icontains (funciona en SQLite) ---
                for probe in probes_clean:
                    try:
                        qs = Producto.objects.filter(empresa=empresa).filter(
                            Q(nombre__icontains=probe) | Q(descripcion__icontains=probe)
                        )[:15]

                        for prod in qs:
                            cur = matches_map.get(prod.id)
                            # Score: 0.5 si matchea nombre, 0.3 si es descripción
                            if prod.nombre and probe.lower() in prod.nombre.lower():
                                score = 0.5
                            else:
                                score = 0.3

                            if not cur or score > cur['score']:
                                serialized = serialize_producto(prod)
                                if serialized:
                                    serialized['score'] = score
                                    matches_map[prod.id] = serialized
                    except Exception as fallback_err:
                        logger.warning(f'Error en fallback icontains "{probe}": {str(fallback_err)[:100]}')
                        continue

            # Retornar matches encontrados
            if matches_map:
                matches = sorted(matches_map.values(), key=lambda x: x.get('score', 0), reverse=True)
                logger.info(f'Encontrados {len(matches)} matches por probes')
                return JsonResponse({'matches': matches})

        # --- ESTRATEGIA 3: Búsqueda por nombre (loose) ---
        if nombre:
            try:
                producto = Producto.objects.filter(empresa=empresa).filter(
                    Q(nombre__icontains=nombre) | Q(descripcion__icontains=nombre)
                ).first()
                if producto:
                    logger.info(f'Encontrado por nombre: {producto.id}')
                    return JsonResponse(serialize_producto(producto))
            except Exception as e:
                logger.warning(f'Error en búsqueda por nombre: {str(e)[:100]}')

        # --- SIN MATCH: Devolver sugerencia para prellenado ---
        logger.info('Sin coincidencias, retornando sugerencia de prellenado')
        return JsonResponse(build_suggestion(None))

    except Exception as e:
        logger.error(f'Error definitivo en prefill_from_scan: {str(e)[:200]}', exc_info=True)
        # NUNCA retornar 500: siempre devolver respuesta valida
        return JsonResponse({
            'error': 'Error procesando solicitud',
            'encontrado': False,
            'matches': []
        }, status=200)  # 200 para que el cliente saiba que llegó pero no hay coincidencias


@login_required
def eliminar_producto(request, producto_id):
    empresa = request.user.empresa
    try:
        producto = Producto.objects.get(id=producto_id, empresa=empresa)
        producto.delete()
        messages.success(request, 'Producto eliminado correctamente.')
    except Producto.DoesNotExist:
        messages.error(request, 'Producto no encontrado o no pertenece a tu empresa.')
    
    return redirect('empresa:listar_productos')
