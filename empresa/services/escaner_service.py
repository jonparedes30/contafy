"""Identificación de productos para el escáner (POS, compras e inventario).

Dos vías, con la misma respuesta:
1. Código leído por la cámara o un lector USB  -> búsqueda exacta (gratis e instantánea).
2. Foto del producto -> Google Vision (logos + texto) -> búsqueda por similitud.

Este módulo no conoce HTTP: la vista solo traduce la petición y la respuesta.
"""
import logging
import re
import unicodedata

import requests
from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__)

# Palabras frecuentes en etiquetas que no ayudan a identificar el producto.
# Se comparan como palabras completas (antes se comparaban como sub-cadenas y
# 'l' o 'g' descartaban cualquier línea con esas letras, p. ej. "COCA COLA").
PALABRAS_RUIDO = {
    'peso', 'neto', 'ingredientes', 'tabla', 'nutricional', 'informacion', 'calorias',
    'proteinas', 'grasas', 'grasa', 'carbohidratos', 'sodio', 'contiene', 'elaborado',
    'conservar', 'fecha', 'lote', 'reg', 'registro', 'sanitario', 'hecho', 'producto',
    'alimento', 'natural', 'artificial', 'cont', 'azucar', 'exceso', 'min', 'max', 'valor',
    'total', 'precio', 'exp', 'pvp', 'consumir', 'antes', 'de', 'del', 'la', 'el', 'en',
    'y', 'con', 'sin', 'para', 'por', 'g', 'kg', 'mg', 'ml', 'l', 'lt', 'litro', 'litros',
    'oz', 'lb', 'gr', 'cc', 'unidades', 'un', 'x',
}

PATRON_NUMEROS = re.compile(r'(?<!\d)(\d{8}|\d{12}|\d{13}|\d{14})(?!\d)')


class EscanerError(Exception):
    """Error con un mensaje seguro para mostrar al usuario."""


def normalizar(texto):
    """Minúsculas, sin tildes y con cualquier signo convertido en espacio."""
    texto = unicodedata.normalize('NFKD', str(texto or '')).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', ' ', texto.lower()).strip()


def palabras_utiles(texto):
    return [p for p in normalizar(texto).split() if len(p) >= 3 and p not in PALABRAS_RUIDO and not p.isdigit()]


def codigo_gtin_valido(codigo):
    """Valida el dígito verificador de EAN-8, UPC-A (12), EAN-13 y GTIN-14."""
    if not codigo or not codigo.isdigit() or len(codigo) not in (8, 12, 13, 14):
        return False
    digitos = [int(d) for d in codigo]
    cuerpo, verificador = digitos[:-1], digitos[-1]
    suma = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(cuerpo)))
    return (10 - suma % 10) % 10 == verificador


def extraer_codigos(texto):
    """Códigos de barras válidos que aparecen en el texto (descarta lotes, registros, teléfonos)."""
    vistos = []
    for numero in PATRON_NUMEROS.findall(texto or ''):
        if codigo_gtin_valido(numero) and numero not in vistos:
            vistos.append(numero)
    return vistos


def buscar_por_codigo(empresa, codigo):
    """Coincidencia exacta por código de barras o código interno."""
    from empresa.models import Producto

    codigo = (codigo or '').strip()
    if not codigo:
        return []
    return list(Producto.objects.filter(empresa=empresa).filter(
        Q(codigo_barras=codigo) | Q(codigo__iexact=codigo)
    )[:5])


def buscar_por_texto(empresa, logos, texto, limite=5):
    """Ordena los productos por cuántas palabras del logo/etiqueta comparten con su nombre."""
    from empresa.models import Producto

    terminos = []
    for fuente in list(logos or []) + (texto or '').splitlines()[:12]:
        for palabra in palabras_utiles(fuente):
            if palabra not in terminos:
                terminos.append(palabra)
    if not terminos:
        return []

    marcas = {p for logo in (logos or []) for p in palabras_utiles(logo)}
    puntuados = []
    for producto in Producto.objects.filter(empresa=empresa, es_servicio=False):
        nombre = set(normalizar(f'{producto.nombre} {producto.descripcion or ""}').split())
        comunes = [t for t in terminos if t in nombre]
        if not comunes:
            continue
        # La marca (logo) pesa más que una palabra suelta de la etiqueta.
        puntaje = len(comunes) + 2 * len(marcas & set(comunes))
        puntuados.append((puntaje, producto))
    puntuados.sort(key=lambda par: (-par[0], par[1].nombre))
    return [p for _, p in puntuados[:limite]]


def analizar_imagen(imagen_b64):
    """Llama a Google Vision y devuelve (logos, texto, etiquetas).

    Nunca deja pasar el mensaje original de `requests`: incluye la URL con la API key.
    """
    api_key = getattr(settings, 'GOOGLE_VISION_API_KEY', '')
    if not api_key:
        raise EscanerError(
            'La identificación por foto no está activada. Escanee el código de barras '
            'o búsquelo por nombre.'
        )
    cuerpo = {'requests': [{
        'image': {'content': imagen_b64},
        'features': [
            {'type': 'LOGO_DETECTION', 'maxResults': 5},
            {'type': 'TEXT_DETECTION', 'maxResults': 1},
            {'type': 'LABEL_DETECTION', 'maxResults': 5},
        ],
    }]}
    try:
        resp = requests.post('https://vision.googleapis.com/v1/images:annotate',
                             params={'key': api_key}, json=cuerpo, timeout=10)
        resp.raise_for_status()
        datos = resp.json()
    except requests.exceptions.Timeout:
        raise EscanerError('El servicio de reconocimiento tardó demasiado. Inténtelo de nuevo.')
    except requests.exceptions.RequestException as e:
        estado = getattr(getattr(e, 'response', None), 'status_code', None)
        logger.error('Google Vision falló (HTTP %s)', estado)
        raise EscanerError('No se pudo analizar la foto en este momento. Escanee el código de barras.')

    respuesta = (datos.get('responses') or [{}])[0]
    if respuesta.get('error'):
        logger.error('Google Vision devolvió error: %s', respuesta['error'].get('message'))
        raise EscanerError('No se pudo analizar la foto. Pruebe con más luz o escanee el código.')

    logos = [a.get('description', '') for a in respuesta.get('logoAnnotations', []) if a.get('description')]
    texto = (respuesta.get('fullTextAnnotation') or {}).get('text', '')
    if not texto and respuesta.get('textAnnotations'):
        texto = respuesta['textAnnotations'][0].get('description', '')
    etiquetas = [a.get('description', '') for a in respuesta.get('labelAnnotations', []) if a.get('description')]
    return logos, texto, etiquetas


def serializar(producto, contexto):
    item = {
        'id': producto.id,
        'nombre': producto.nombre,
        'codigo': producto.codigo or '',
        'codigo_barras': producto.codigo_barras or '',
        'stock': producto.stock,
        'categoria': producto.categoria.nombre if producto.categoria_id else '',
        'precio_unitario': float(producto.precio_unitario or 0),
        'pvp': float(producto.pvp or 0),
        'stock_minimo': producto.stock_minimo or 0,
    }
    precio_venta = float(producto.pvp or producto.precio_unitario or 0)
    item.update({'precio_venta': precio_venta, 'precio': precio_venta,
                 'ultimo_costo': item['precio_unitario'], 'stock_disponible': producto.stock})
    return item


# --- Catálogo público de productos (Open Food Facts) ---------------------------
# Base de datos abierta y gratuita, sin clave. Solo se envía el número del código.
# Sirve para sugerir nombre y marca al registrar un producto nuevo.
CATALOGO_URL = 'https://world.openfoodfacts.org/api/v2/product/{codigo}.json'
CATALOGO_CAMPOS = 'product_name_es,product_name,generic_name_es,brands,quantity,categories'


def buscar_en_catalogo_publico(codigo):
    """Sugerencia {nombre, marca, presentacion, categoria, fuente} o None.

    Nunca lanza excepciones: si el servicio no responde, simplemente no hay sugerencia.
    El resultado (también el "no encontrado") se guarda 1 día en caché.
    """
    from django.core.cache import cache

    codigo = (codigo or '').strip()
    if not getattr(settings, 'CATALOGO_PUBLICO_ACTIVO', True) or not codigo_gtin_valido(codigo):
        return None
    clave = f'catalogo_publico:{codigo}'
    en_cache = cache.get(clave)
    if en_cache is not None:
        return en_cache or None

    sugerencia = {}
    try:
        resp = requests.get(CATALOGO_URL.format(codigo=codigo), params={'fields': CATALOGO_CAMPOS},
                            headers={'User-Agent': 'Contafy/1.0 (contabilidad para PYMES; Ecuador)'},
                            timeout=4)
        if resp.status_code == 200:
            datos = resp.json()
            producto = datos.get('product') or {}
            nombre = (producto.get('product_name_es') or producto.get('product_name')
                      or producto.get('generic_name_es') or '').strip()
            if datos.get('status') == 1 and nombre:
                # La "marca" suele venir como razón social (p. ej. "COCA-COLA SERVICES SA/NV"):
                # se sugiere aparte, sin pegarla al nombre.
                marca = (producto.get('brands') or '').split(',')[0].strip()
                presentacion = re.sub(r'\s*[℮e]$', '', (producto.get('quantity') or '').strip())
                if presentacion and presentacion.lower() not in nombre.lower():
                    nombre = f'{nombre} {presentacion}'
                categorias = [c.strip() for c in (producto.get('categories') or '').split(',')
                              if c.strip() and ':' not in c]
                sugerencia = {
                    'nombre': nombre[:100],
                    'marca': marca[:60],
                    'presentacion': presentacion[:40],
                    'categoria': categorias[-1][:60] if categorias else '',
                    'fuente': 'Open Food Facts',
                }
    except (requests.exceptions.RequestException, ValueError):
        logger.info('Catálogo público sin respuesta para %s', codigo)
        return None  # sin caché: puede ser un corte momentáneo

    cache.set(clave, sugerencia, 60 * 60 * 24)
    return sugerencia or None


def identificar(empresa, contexto='compra', codigo=None, imagen_b64=None):
    """Punto de entrada único. Devuelve el dict de respuesta del escáner."""
    logos, texto, etiquetas, origen = [], '', [], 'codigo'
    codigos = [codigo.strip()] if codigo and codigo.strip() else []

    if not codigos:
        if not imagen_b64:
            raise EscanerError('No se recibió ni un código ni una foto.')
        origen = 'foto'
        logos, texto, etiquetas = analizar_imagen(imagen_b64)
        codigos = extraer_codigos(texto)

    productos, codigo_detectado = [], codigos[0] if codigos else ''
    for c in codigos:
        productos = buscar_por_codigo(empresa, c)
        if productos:
            codigo_detectado = c
            break
    if not productos and origen == 'foto':
        productos = buscar_por_texto(empresa, logos, texto)

    mensaje, motivo, sin_stock = '', '', None
    if contexto == 'venta' and productos:
        con_stock = [p for p in productos if p.es_servicio or p.stock > 0]
        if not con_stock:
            mensaje = f'"{productos[0].nombre}" no tiene stock disponible.'
            motivo, sin_stock = 'sin_stock', serializar(productos[0], contexto)
        productos = con_stock

    lista = [serializar(p, contexto) for p in productos]
    if not lista and not mensaje:
        motivo = 'no_existe'
        mensaje = (f'No hay ningún producto con el código {codigo_detectado}.' if codigo_detectado
                   else 'No se reconoció el producto. Pruebe escaneando el código de barras.')
    return {
        'success': True, 'ok': True,
        'found': bool(lista),
        'productos': lista, 'products': lista,
        'codigo_detectado': codigo_detectado,
        'origen': origen,
        'mensaje': mensaje,
        # Por qué no hay resultado: 'no_existe' (ofrecer registrarlo) o 'sin_stock' (ofrecer una compra)
        'motivo': motivo,
        'producto_sin_stock': sin_stock,
        'meta': {'total': len(lista), 'contexto': contexto, 'api_version': '3.0'},
        'debug': {'logos': logos, 'textos': [l for l in texto.splitlines() if l.strip()][:5],
                  'labels': etiquetas[:5], 'search_terms': palabras_utiles(' '.join(logos))[:3]},
    }
