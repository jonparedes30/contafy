#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

# Leer archivo
with open('empresa/views/productos.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar start y end de la función
start_marker = '@login_required\ndef prefill_producto_from_scan(request):'
start_idx = content.find(start_marker)

if start_idx == -1:
    print("ERROR: Function not found")
    sys.exit(1)

# Buscar el final
remaining = content[start_idx + len(start_marker):]
next_func_idx = remaining.find('\n\n@login_required\ndef ')
if next_func_idx == -1:
    next_func_idx = remaining.find('\n\n@')

end_idx = start_idx + len(start_marker) + next_func_idx

# Nueva función mejorada
new_function = '''@login_required
def prefill_producto_from_scan(request):
    """
    Buscar producto en inventario desde vision detection.

    Retorna:
    - Si encontro: {found: true, matches: [productos]}
    - Si no: {found: false, prefill: {datos para formulario}}
    """
    if request.method != 'POST':
        return JsonResponse({'found': False, 'error': 'POST required'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except:
        return JsonResponse({'found': False, 'matches': []}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({'found': False, 'matches': []}, status=400)

    if not request.user.is_authenticated:
        return JsonResponse({'found': False, 'error': 'Not authenticated'}, status=401)

    empresa = getattr(request.user, 'empresa', None)
    if not empresa:
        return JsonResponse({'found': False, 'error': 'No empresa'}, status=403)

    # Extract data
    detection = payload.get('detection', {}) or {}

    barcode = None
    try:
        barcodes = detection.get('barcodes', []) or []
        if isinstance(barcodes, list) and barcodes:
            barcode = str(barcodes[0]).strip() if barcodes[0] else None
        if not barcode:
            barcode = str(payload.get('barcode') or payload.get('codigo_barras') or '').strip() or None
    except:
        barcode = None

    ocr_texts = []
    try:
        ocr = detection.get('ocr', []) or []
        ocr_texts = [str(t).strip() for t in ocr if t and str(t).strip()]
    except:
        pass

    logos = []
    try:
        logos_data = detection.get('logos', []) or []
        logos = [str(l).strip() for l in logos_data if l and str(l).strip()]
    except:
        pass

    nombre = str(payload.get('nombre', '') or '').strip() or None
    marca = str(payload.get('marca', '') or '').strip() or None
    descripcion = str(payload.get('descripcion', '') or '').strip() or None

    try:
        precio = float(payload.get('precio_unitario') or 0) or 0
    except:
        precio = 0

    def serialize_producto(producto, score=None):
        try:
            result = {
                'id': producto.id,
                'nombre': str(producto.nombre or ''),
                'marca': str(getattr(producto, 'marca', '') or ''),
                'descripcion': str(producto.descripcion or ''),
                'codigo': str(producto.codigo or ''),
                'codigo_barras': str(producto.codigo_barras or ''),
                'precio_unitario': float(producto.precio_unitario or 0),
                'stock': int(producto.stock or 0),
            }
            if score is not None:
                result['score'] = round(score, 2)
            return result
        except Exception as e:
            logger.error(f'Serialize error: {str(e)[:100]}')
            return None

    def score_match(prod, term):
        if not term: return 0
        term = term.lower()
        if term == (prod.nombre or '').lower(): return 1.0
        if term in (prod.nombre or '').lower(): return 0.8
        if term in (prod.descripcion or '').lower(): return 0.5
        if term[:min(3, len(term))] in (prod.nombre or '').lower(): return 0.3
        return 0

    matches_map = {}

    try:
        # Search by barcode
        if barcode:
            try:
                prod = Producto.objects.filter(empresa=empresa).filter(
                    Q(codigo_barras__iexact=barcode) | Q(codigo__iexact=barcode)
                ).first()
                if prod:
                    logger.info(f'Barcode match: {prod.id}')
                    s = serialize_producto(prod, score=1.0)
                    if s: matches_map[prod.id] = s
            except Exception as e:
                logger.warning(f'Barcode error: {str(e)[:100]}')

        # Search by OCR texts
        if ocr_texts:
            for text in ocr_texts[:3]:
                try:
                    qs = Producto.objects.filter(empresa=empresa).filter(
                        Q(nombre__icontains=text) | Q(descripcion__icontains=text)
                    )[:15]
                    for prod in qs:
                        score = score_match(prod, text)
                        if score > 0:
                            existing = matches_map.get(prod.id)
                            if not existing or score > existing.get('score', 0):
                                s = serialize_producto(prod, score=score)
                                if s: matches_map[prod.id] = s
                except:
                    pass

        # Search by logos
        if logos:
            for logo in logos[:2]:
                try:
                    qs = Producto.objects.filter(empresa=empresa).filter(
                        Q(nombre__icontains=logo) | Q(descripcion__icontains=logo)
                    )[:10]
                    for prod in qs:
                        score = 0.6 if logo.lower() in (prod.nombre or '').lower() else 0.4
                        existing = matches_map.get(prod.id)
                        if not existing or score > existing.get('score', 0):
                            s = serialize_producto(prod, score=score)
                            if s: matches_map[prod.id] = s
                except:
                    pass

        # Search by direct name/brand
        search_terms = [t for t in [nombre, marca] if t]
        for term in search_terms[:2]:
            try:
                qs = Producto.objects.filter(empresa=empresa).filter(
                    Q(nombre__icontains=term) | Q(descripcion__icontains=term)
                )[:10]
                for prod in qs:
                    score = score_match(prod, term)
                    if score > 0:
                        existing = matches_map.get(prod.id)
                        if not existing or score > existing.get('score', 0):
                            s = serialize_producto(prod, score=score)
                            if s: matches_map[prod.id] = s
            except:
                pass

        # Return matches if found
        if matches_map:
            matches = sorted(matches_map.values(), key=lambda x: x.get('score', 0), reverse=True)
            logger.info(f'Found {len(matches)} matches')
            return JsonResponse({
                'found': True,
                'matches': matches,
                'mensaje': f'Se encontraron {len(matches)} producto(s)'
            })

        # No matches: return prefill
        logger.info('No matches')
        return JsonResponse({
            'found': False,
            'matches': [],
            'prefill': {
                'nombre': nombre or (ocr_texts[0] if ocr_texts else ''),
                'marca': marca or '',
                'descripcion': descripcion or '',
                'codigo_barras': barcode or '',
                'precio_unitario': precio or 0,
            },
            'mensaje': 'Producto no encontrado. Completa para agregarlo.'
        })

    except Exception as e:
        logger.error(f'Prefill error: {str(e)[:200]}', exc_info=True)
        return JsonResponse({
            'found': False,
            'matches': [],
            'prefill': {
                'nombre': nombre or '',
                'marca': marca or '',
                'descripcion': descripcion or '',
                'codigo_barras': barcode or '',
                'precio_unitario': precio or 0,
            }
        }, status=200)

'''

# Replace
new_content = content[:start_idx] + new_function + content[end_idx:]

# Write back
with open('empresa/views/productos.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: Function updated!")
