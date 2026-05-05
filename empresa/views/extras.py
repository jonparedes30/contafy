from django.http import JsonResponse
from empresa.models import Producto
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import requests

# Pos identifier
from core.pos_identifier import identify_products
from django.contrib.auth.decorators import login_required
from django.db import transaction
import uuid


def obtener_info_producto(request):
    """Devuelve información del producto al escanear el código."""
    codigo = request.GET.get('codigo')
    producto = Producto.objects.filter(codigo=codigo).first()
    if producto:
        data = {
            'id': producto.id,
            'nombre': producto.nombre,
            'precio_unitario': float(producto.precio_unitario),
            'stock': producto.stock,
        }
    else:
        data = {'error': 'Producto no encontrado'}
    return JsonResponse(data)


@csrf_exempt
def vision_recognize(request):
    """Recibe una imagen (base64) y consulta Google Vision API (logo/label/text).

    Espera JSON POST: {"image": "data:image/jpeg;base64,..."}
    Devuelve JSON con estructuras: logos, labels, texts
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        image_b64 = payload.get('image')
        if not image_b64:
            return JsonResponse({'error': 'No image provided'}, status=400)

        # limpiar prefijo data URL si existe
        if image_b64.startswith('data:'):
            image_b64 = image_b64.split(',', 1)[1]

        api_key = getattr(settings, 'GOOGLE_VISION_API_KEY', None)
        if not api_key:
            return JsonResponse({'error': 'GOOGLE_VISION_API_KEY not configured'}, status=500)

        url = f'https://vision.googleapis.com/v1/images:annotate?key={api_key}'
        body = {
            'requests': [
                {
                    'image': {'content': image_b64},
                    'features': [
                        {'type': 'LOGO_DETECTION', 'maxResults': 5},
                        {'type': 'LABEL_DETECTION', 'maxResults': 8},
                        {'type': 'TEXT_DETECTION', 'maxResults': 5}
                    ]
                }
            ]
        }

        resp = requests.post(url, json=body, timeout=15)
        resp.raise_for_status()
        vision_json = resp.json()

        # Normalizar respuesta
        result = {'logos': [], 'labels': [], 'texts': []}
        responses = vision_json.get('responses', [])
        if responses:
            r = responses[0]
            for l in r.get('logoAnnotations', []):
                result['logos'].append({'description': l.get('description'), 'score': l.get('score')})
            for lab in r.get('labelAnnotations', []):
                result['labels'].append({'description': lab.get('description'), 'score': lab.get('score')})
            full_text = r.get('fullTextAnnotation')
            if full_text and full_text.get('text'):
                result['texts'].append(full_text.get('text'))
        # Usar identificador POS para generar output consistente
        try:
            payload_for_id = {
                'logos': [l.get('description') for l in result.get('logos', []) if l.get('description')],
                'ocr': result.get('texts', []),
                'barcodes': [],
            }

            # Extraer posibles códigos de barras del texto
            import re
            if result.get('texts'):
                m = re.search(r"\b(\d{8,13})\b", "\n".join(result['texts']))
                if m:
                    payload_for_id['barcodes'].append(m.group(1))

            # Construir products_db limitado a la empresa del usuario si disponible
            qs = Producto.objects.all()
            # si request.user tiene empresa, filtrar
            if getattr(request, 'user', None) and getattr(request.user, 'empresa', None):
                qs = qs.filter(empresa=request.user.empresa)

            products_db = []
            for p in qs[:500]:
                products_db.append({
                    'id': p.id,
                    'nombre': p.nombre,
                    'marca': getattr(p, 'marca', '') or '',
                    'presentacion': p.descripcion or '',
                    'barcode': p.codigo_barras or '',
                    'sku': p.codigo or '',
                })

            detection = identify_products(payload_for_id, products_db, modo='single' if len(payload_for_id.get('logos', [])) < 2 else 'multi', context='venta')
        except Exception:
            detection = {'modo': 'single', 'producto': {'id':'','nombre':'','marca':'','presentacion':'','confianza':0.0}, 'accion': 'no_detectado'}

        return JsonResponse({'ok': True, 'results': result, 'detection': detection})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)


@csrf_exempt
def create_product_from_scan(request):
    """Crear producto en inventario a partir de payload del escáner.

    POST JSON esperado: {
        'nombre': str (opcional),
        'marca': str (opcional),
        'presentacion': str (opcional),
        'barcode': str (opcional),
        'stock': int (opcional),
        'precio_unitario': number (opcional)
    }
    Si se envía solo detection (logos/ocr/barcodes), intentará extraer barcode/nombre.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'JSON inválido: {e}'}, status=400)

    empresa = getattr(request.user, 'empresa', None)
    if not empresa:
        return JsonResponse({'success': False, 'error': 'Usuario no asociado a empresa'}, status=400)

    # Extraer campos
    barcode = payload.get('barcode') or None
    nombre = payload.get('nombre') or None
    marca = payload.get('marca') or None
    presentacion = payload.get('presentacion') or ''
    stock = int(payload.get('stock') or 0)
    precio = payload.get('precio_unitario')

    # Si solo viene detection, intentar obtener barcode/ocr
    if not barcode and payload.get('detection'):
        det = payload.get('detection', {})
        bcodes = det.get('barcodes') or []
        if bcodes:
            barcode = bcodes[0]
        elif det.get('ocr'):
            nombre = nombre or (det.get('ocr')[0] if det.get('ocr') else None)

    try:
        with transaction.atomic():
            # Si existe por barcode en la empresa, devolver existente
            if barcode:
                existing = Producto.objects.filter(empresa=empresa, codigo_barras=barcode).first()
                if existing:
                    return JsonResponse({'success': True, 'created': False, 'product': {
                        'id': existing.id,
                        'nombre': existing.nombre,
                        'stock': existing.stock,
                        'precio_unitario': float(existing.precio_unitario) if existing.precio_unitario is not None else None,
                        'codigo_barras': existing.codigo_barras
                    }})

            # Generar codigo único interno
            codigo = f"SCAN-{uuid.uuid4().hex[:8]}"

            producto = Producto.objects.create(
                empresa=empresa,
                codigo=codigo,
                codigo_barras=barcode or None,
                nombre=nombre or (marca or 'Producto escaneado'),
                descripcion=presentacion or '',
                precio_unitario=precio or 0,
                pvp=precio or 0,
                stock=stock
            )

            return JsonResponse({'success': True, 'created': True, 'product': {
                'id': producto.id,
                'nombre': producto.nombre,
                'stock': producto.stock,
                'precio_unitario': float(producto.precio_unitario) if producto.precio_unitario is not None else None,
                'codigo_barras': producto.codigo_barras
            }})

    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)


@csrf_exempt
def prefill_compra_from_scan(request):
    """Prefill datos para crear una compra a partir del escaneo.

    POST JSON esperado: { 'barcode': '...', 'detection': {...} }
    Responde con product data si existe en inventario de la empresa, o status no_encontrado.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'JSON inválido: {e}'}, status=400)

    empresa = getattr(request.user, 'empresa', None)
    if not empresa:
        return JsonResponse({'success': False, 'error': 'Usuario sin empresa'}, status=400)

    barcode = payload.get('barcode')
    detection = payload.get('detection') or {}

    # Buscar por barcode
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

    # Intentar por texto OCR / logos
    ocr_texts = detection.get('ocr', []) if isinstance(detection, dict) else []
    candidate = None
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
