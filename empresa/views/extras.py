from django.http import JsonResponse
from empresa.models import Producto
from django.conf import settings
import json
import logging
import requests

# Pos identifier
from core.pos_identifier import identify_products
from django.contrib.auth.decorators import login_required



logger = logging.getLogger(__name__)

@login_required
def obtener_info_producto(request):
    """Devuelve información del producto buscando por código interno o código de barras."""
    codigo = request.GET.get('codigo', '').strip()
    empresa = getattr(request.user, 'empresa', None)
    if not empresa:
        return JsonResponse({'error': 'Usuario no asociado a empresa'}, status=400)
    # Buscar primero por código interno, luego por código de barras
    producto = (
        Producto.objects.filter(codigo=codigo, empresa=empresa).first()
        or Producto.objects.filter(codigo_barras=codigo, empresa=empresa).first()
    )
    if producto:
        data = {
            'id': producto.id,
            'nombre': producto.nombre,
            'precio_unitario': float(producto.precio_unitario) if producto.precio_unitario else 0,
            'stock': producto.stock,
        }
    else:
        data = {'error': 'Producto no encontrado'}
    return JsonResponse(data)


@login_required
def vision_recognize(request):
    """Recibe una imagen (base64) y consulta Google Vision API (logo/label/text).

    Espera JSON POST: {"image": "data:image/jpeg;base64,..."}
    Devuelve JSON con estructuras: logos, labels, texts
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not getattr(request.user, 'empresa', None):
        return JsonResponse({'error': 'Usuario no asociado a empresa'}, status=400)

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
    except Exception:
        # No devolver str(exc): el error de requests incluye la URL con la API key.
        logger.exception('Error en vision_recognize')
        return JsonResponse({'error': 'No se pudo analizar la foto en este momento.'}, status=500)

