"""Crea el asiento contable de los aportes/retiros de capital ya registrados.

Hasta ahora Capital.save() no generaba asiento (estaba deshabilitado) y la vista
del Balance General compensaba sumando el modelo Capital "por fuera" como
"Caja (Capital)". La vista de capital ya registra el asiento, así que aquí se
asientan los registros previos y se retira esa compensación (ver
views/contabilidad.balance_general). Se omiten los que ya tienen su asiento.
"""
import uuid

from django.db import migrations


def _cuenta(CuentaContable, empresa, nombre, tipo):
    cuenta = CuentaContable.objects.filter(empresa=empresa, nombre__iexact=nombre).first()
    return cuenta or CuentaContable.objects.create(empresa=empresa, nombre=nombre, tipo=tipo)


def asentar_capital(apps, schema_editor):
    Capital = apps.get_model('empresa', 'Capital')
    CuentaContable = apps.get_model('empresa', 'CuentaContable')
    MovimientoContable = apps.get_model('empresa', 'MovimientoContable')

    for capital in Capital.objects.select_related('empresa').order_by('id'):
        es_aporte = capital.tipo == 'aporte'
        descripcion = f"{'Aporte' if es_aporte else 'Retiro'} de capital: {capital.descripcion}"
        ya_asentado = MovimientoContable.objects.filter(
            empresa=capital.empresa, descripcion=descripcion, monto=capital.monto
        ).exists()
        if ya_asentado:
            continue

        caja = _cuenta(CuentaContable, capital.empresa, 'Caja', 'activo')
        cuenta_capital = _cuenta(CuentaContable, capital.empresa, 'Capital', 'capital')
        debito, credito = (caja, cuenta_capital) if es_aporte else (cuenta_capital, caja)
        transaccion_id = str(uuid.uuid4())[:12]
        for cuenta, tipo in ((debito, 'debito'), (credito, 'credito')):
            mov = MovimientoContable.objects.create(
                empresa=capital.empresa, cuenta_fk=cuenta, cuenta_text=cuenta.nombre,
                tipo=tipo, monto=capital.monto, descripcion=descripcion,
                transaccion_id=transaccion_id,
            )
            # `fecha` es auto_now_add: se corrige después para respetar la fecha del aporte.
            MovimientoContable.objects.filter(pk=mov.pk).update(fecha=capital.fecha)


class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0031_producto_es_servicio'),
    ]

    operations = [
        migrations.RunPython(asentar_capital, migrations.RunPython.noop),
    ]
