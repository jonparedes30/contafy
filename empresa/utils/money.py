from decimal import Decimal, ROUND_HALF_UP

# Small monetary helpers used across the project to avoid float inaccuracies
MONEDA_PLACES = Decimal('0.01')

def to_decimal(value):
    """Convert value to Decimal safely.

    Accepts Decimal, int, float, str. Floats are converted by str() to
    avoid binary float artifacts.
    """
    if isinstance(value, Decimal):
        return value.quantize(MONEDA_PLACES, rounding=ROUND_HALF_UP)
    try:
        return Decimal(str(value or '0')).quantize(MONEDA_PLACES, rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal('0.00')

def quantize_currency(d):
    if not isinstance(d, Decimal):
        d = to_decimal(d)
    return d.quantize(MONEDA_PLACES, rounding=ROUND_HALF_UP)


class MontoInvalido(ValueError):
    """El usuario ingresó un monto que no se puede interpretar."""


def parse_monto(value, campo='Monto', permitir_vacio=False):
    """Convierte lo que escribe el usuario en Decimal con 2 decimales.

    Acepta "10.50", "10,50", "1.234,56" y "1,234.56". A diferencia de
    to_decimal(), no oculta errores: lanza MontoInvalido con un mensaje
    listo para mostrar al usuario.
    """
    if isinstance(value, Decimal):
        return value.quantize(MONEDA_PLACES, rounding=ROUND_HALF_UP)
    if isinstance(value, (int, float)):
        return Decimal(str(value)).quantize(MONEDA_PLACES, rounding=ROUND_HALF_UP)

    texto = str(value or '').strip().replace('$', '').replace(' ', '')
    if not texto:
        if permitir_vacio:
            return Decimal('0.00')
        raise MontoInvalido(f'{campo}: ingresa un valor.')

    # El último separador es el decimal; los demás son de miles.
    # Excepción: con 3 dígitos detrás ("1.234") es separador de miles,
    # porque un monto en dólares nunca lleva 3 decimales.
    ultimo = max(texto.rfind(','), texto.rfind('.'))
    if ultimo != -1:
        entero = texto[:ultimo].replace(',', '').replace('.', '')
        decimales = texto[ultimo + 1:]
        texto = f'{entero}{decimales}' if len(decimales) == 3 else f'{entero}.{decimales}'
    try:
        return Decimal(texto).quantize(MONEDA_PLACES, rounding=ROUND_HALF_UP)
    except Exception:
        raise MontoInvalido(f'{campo}: "{value}" no es un número válido.')
