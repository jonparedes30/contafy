"""Saldos de cuentas contables calculados desde los movimientos."""
from decimal import Decimal

from django.db.models import Sum

# Cuentas cuyo saldo crece con débitos; el resto (pasivo, capital, ingreso) crece con créditos.
TIPOS_DEUDORES = ('activo', 'gasto')


def saldo_cuenta(empresa, nombre_cuenta):
    """Saldo actual de la cuenta según su naturaleza. Devuelve 0 si no existe."""
    from empresa.models import CuentaContable, MovimientoContable

    cuenta = CuentaContable.objects.filter(empresa=empresa, nombre__iexact=nombre_cuenta).first()
    if not cuenta:
        return Decimal('0.00')
    movs = MovimientoContable.objects.filter(empresa=empresa, cuenta_fk=cuenta)
    debitos = Decimal(movs.filter(tipo='debito').aggregate(s=Sum('monto'))['s'] or 0)
    creditos = Decimal(movs.filter(tipo='credito').aggregate(s=Sum('monto'))['s'] or 0)
    saldo = debitos - creditos if cuenta.tipo in TIPOS_DEUDORES else creditos - debitos
    return saldo.quantize(Decimal('0.01'))


# Palabras que identifican activos no corrientes (no se convierten en efectivo en el corto plazo).
ACTIVO_NO_CORRIENTE = (
    'maquinaria', 'equipo', 'vehículo', 'vehiculo', 'edificio', 'terreno', 'mueble',
    'activo fijo', 'propiedad', 'depreciación', 'depreciacion', 'intangible',
)


def resumen_balance(empresa):
    """Totales del balance a partir de los movimientos (no del saldo inicial de la cuenta).

    Devuelve Decimal: activo_corriente, activo_total, pasivo_total, capital.
    """
    from empresa.models import CuentaContable

    totales = {'activo_corriente': Decimal('0'), 'activo_total': Decimal('0'),
               'pasivo_total': Decimal('0'), 'capital': Decimal('0')}
    for cuenta in CuentaContable.objects.filter(empresa=empresa, tipo__in=('activo', 'pasivo', 'capital')):
        saldo = saldo_cuenta(empresa, cuenta.nombre)
        if cuenta.tipo == 'activo':
            totales['activo_total'] += saldo
            if not any(p in cuenta.nombre.lower() for p in ACTIVO_NO_CORRIENTE):
                totales['activo_corriente'] += saldo
        elif cuenta.tipo == 'pasivo':
            totales['pasivo_total'] += saldo
        elif cuenta.nombre.lower() != 'ventas':
            # 'Ventas' a veces queda con tipo capital por datos antiguos; es ingreso, no patrimonio.
            totales['capital'] += saldo
    return totales


def flujo_cuenta(empresa, nombre_cuenta, desde, hasta):
    """Movimiento neto de una cuenta entre dos fechas (inclusive), según su naturaleza."""
    from empresa.models import CuentaContable, MovimientoContable

    cuenta = CuentaContable.objects.filter(empresa=empresa, nombre__iexact=nombre_cuenta).first()
    if not cuenta:
        return Decimal('0.00')
    movs = MovimientoContable.objects.filter(
        empresa=empresa, cuenta_fk=cuenta, fecha__date__gte=desde, fecha__date__lte=hasta
    )
    debitos = Decimal(movs.filter(tipo='debito').aggregate(s=Sum('monto'))['s'] or 0)
    creditos = Decimal(movs.filter(tipo='credito').aggregate(s=Sum('monto'))['s'] or 0)
    saldo = debitos - creditos if cuenta.tipo in TIPOS_DEUDORES else creditos - debitos
    return saldo.quantize(Decimal('0.01'))


def estado_resultados_periodo(empresa, desde, hasta):
    """Ventas, costo, gastos y utilidades de un período, desde el libro contable."""
    ventas = flujo_cuenta(empresa, 'Ventas', desde, hasta)
    costo = flujo_cuenta(empresa, 'Costo de Ventas', desde, hasta)
    gastos = flujo_cuenta(empresa, 'Gastos', desde, hasta)
    utilidad_bruta = ventas - costo
    utilidad_neta = utilidad_bruta - gastos
    return {
        'ventas': ventas, 'costo_ventas': costo, 'gastos': gastos,
        'utilidad_bruta': utilidad_bruta, 'utilidad_neta': utilidad_neta,
        'margen_neto': (utilidad_neta / ventas * 100) if ventas else Decimal('0'),
    }
