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
