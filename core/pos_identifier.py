from typing import List, Dict, Optional
from difflib import SequenceMatcher
import json


def _similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _compute_confidence(product: Dict, payload: Dict) -> float:
    # Exact barcode/sku match -> highest confidence
    barcodes = payload.get("barcodes", []) or []
    for code in barcodes:
        if not code:
            continue
        if str(code) == str(product.get("barcode")) or str(code) == str(product.get("sku")):
            return 1.0

    # Brand/logo boost
    logos = payload.get("logos", []) or []
    brand_boost = 0.0
    for l in logos:
        if not l:
            continue
        if l.lower() == (product.get("marca") or "").lower():
            brand_boost = max(brand_boost, 0.20)

    # OCR texts -> compare against name, presentacion, marca
    ocr_texts = payload.get("ocr", []) or []
    best_ratio = 0.0
    for t in ocr_texts:
        if not t:
            continue
        r_name = _similar(t, product.get("nombre", "")) * 0.6
        r_pres = _similar(t, product.get("presentacion", "")) * 0.3
        r_brand = _similar(t, product.get("marca", "")) * 0.1
        best_ratio = max(best_ratio, r_name + r_pres + r_brand)

    # Combine
    confidence = min(1.0, best_ratio + brand_boost)
    return confidence


def identify_products(
    payload: Dict,
    products_db: List[Dict],
    existing_cart: Optional[List[Dict]] = None,
    modo: str = "single",
    context: str = "venta",
) -> Dict:
    """
    payload: { 'logos': [str], 'ocr': [str], 'barcodes': [str] }
    products_db: list of products with keys: id, nombre, marca, presentacion, barcode, sku
    existing_cart: list of items with keys: product_id, cantidad
    modo: 'single' or 'multi'

    Returns a dict matching the JSON schema required by the POS.
    """
    if existing_cart is None:
        existing_cart = []

    # Compute confidences for all products
    scored = []
    for p in products_db:
        conf = _compute_confidence(p, payload)
        scored.append((conf, p))

    scored.sort(key=lambda x: x[0], reverse=True)

    if modo == "single":
        best_conf, best_p = (scored[0] if scored else (0.0, None))
        action = "no_detectado"
        mensaje = None

        if best_p is not None:
            if best_conf >= 0.85:
                action = "auto_agregar"
            elif best_conf >= 0.60:
                action = "confirmar"
            else:
                action = "no_detectado"

            producto = {
                "id": str(best_p.get("id")),
                "nombre": best_p.get("nombre", ""),
                "marca": best_p.get("marca", ""),
                "presentacion": best_p.get("presentacion", ""),
                "confianza": round(float(best_conf), 2),
            }
        else:
            producto = {"id": "", "nombre": "", "marca": "", "presentacion": "", "confianza": 0.0}

        # En modo venta, si no hay coincidencia clara, devolver mensaje no registrado
        if context == 'venta' and action == 'no_detectado':
            mensaje = 'Producto no registrado en inventario'

        out = {"modo": "single", "producto": producto, "accion": action}
        if mensaje:
            out["mensaje"] = mensaje
        return out

    # multi
    results = []
    # Heuristic: include candidates with confidence >= 0.60
    for conf, p in scored:
        if conf < 0.60:
            break
        action = "confirmar"
        if conf >= 0.85:
            action = "auto_agregar"
        results.append(
            {
                "id": str(p.get("id")),
                "nombre": p.get("nombre", ""),
                "marca": p.get("marca", ""),
                "presentacion": p.get("presentacion", ""),
                "confianza": round(float(conf), 2),
                "accion": action,
            }
        )

    # En modo venta, si no hay resultados claros, no bloquear — devolver lista vacía
    if context == 'venta' and len(results) == 0:
        return {"modo": "multi", "productos": []}

    return {"modo": "multi", "productos": results}


def dumps_json(result: Dict) -> str:
    """Return a compact JSON string (to be sent as model output)."""
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))
