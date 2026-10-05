"""Asiento contable de aportes y retiros de capital."""
from empresa.views.contabilidad import registrar_movimiento_contable


def descripcion_asiento(capital):
    return f"{'Aporte' if capital.tipo == 'aporte' else 'Retiro'} de capital: {capital.descripcion}"


def registrar_asiento_capital(capital):
    """Aporte: Débito Caja / Crédito Capital. Retiro: al revés."""
    es_aporte = capital.tipo == 'aporte'
    registrar_movimiento_contable(
        empresa=capital.empresa,
        cuenta_debito_nombre='Caja' if es_aporte else 'Capital',
        cuenta_credito_nombre='Capital' if es_aporte else 'Caja',
        monto=capital.monto,
        descripcion=descripcion_asiento(capital),
        tipo_cuenta_debito='activo' if es_aporte else 'capital',
        tipo_cuenta_credito='capital' if es_aporte else 'activo',
    )
