"""
Management command: reset_demos

Deja las 3 empresas demo (demo_comercio, demo_manufactura, demo_servicios)
listas para el siguiente visitante:

1. Elimina lo creado por visitantes (creado_en > PROTECTION_DATE), registro por
   registro, para que cada borrado revierta sus asientos contables y reponga
   el stock.
2. "Rejuvenece" los datos originales: desplaza todas sus fechas para que la
   última venta sea de ayer. Así los reportes del mes, el selector de demos y
   los gráficos siempre muestran actividad reciente.
3. Enlaza los asientos de los datos sembrados con su documento y les copia
   la fecha (vincular_asientos_huerfanos).
4. Iguala la cuenta Inventario con el stock físico (regularizar_inventario).

Se identifica lo creado por visitantes con `creado_en` (fecha real de alta) y
no con `fecha`, porque `fecha` se desplaza en el paso 2.

Uso:
    python manage.py reset_demos
    python manage.py reset_demos --dry-run
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Max
from django.utils import timezone

DEMO_USERNAMES = ['demo_comercio', 'demo_manufactura', 'demo_servicios']

# Todo lo creado ANTES o EN esta fecha son los datos originales de la demo.
# NO cambiar este valor.
PROTECTION_DATE = timezone.make_aware(datetime(2026, 5, 22, 23, 59, 59))

# (modelo, campos de fecha que se desplazan al rejuvenecer)
CAMPOS_FECHA = [
    ('Venta', ['fecha']),
    ('Compra', ['fecha']),
    ('Gasto', ['fecha']),
    ('Capital', ['fecha']),
    ('MovimientoContable', ['fecha']),
    ('MovimientoInventario', ['fecha']),
    ('CuentaPorCobrar', ['fecha_vencimiento']),
    ('CuentaPorPagar', ['fecha_vencimiento']),
    ('PagoCuentaPorCobrar', ['fecha_pago']),
    ('PagoCuentaPorPagar', ['fecha_pago']),
    ('ContratoVenta', ['fecha_inicio', 'fecha_fin']),
    ('OrdenProduccion', ['fecha_inicio', 'fecha_fin']),
    ('ConsumoMateriaPrima', ['fecha_consumo']),
    ('Producto', ['fecha_vencimiento']),
]

# Registros de visitantes sin lógica de borrado propia, en orden seguro (hijos primero).
MODELOS_VISITANTE = [
    'PagoCuentaPorCobrar', 'PagoCuentaPorPagar', 'CuentaPorCobrar', 'CuentaPorPagar',
    'MovimientoInventario', 'MovimientoContable', 'Capital', 'MetaFinanciera',
    'Producto', 'Cliente', 'Proveedor',
]


def _modelo(nombre):
    from django.apps import apps
    return apps.get_model('empresa', nombre)


def eliminar_datos_visitantes(empresa):
    """Borra lo creado tras PROTECTION_DATE revirtiendo stock y asientos. Devuelve cuántos registros borró."""
    Venta, Compra, Gasto = _modelo('Venta'), _modelo('Compra'), _modelo('Gasto')
    nuevos = {'empresa': empresa, 'creado_en__gt': PROTECTION_DATE}
    total = 0

    for venta in Venta.objects.filter(**nuevos).select_related('producto'):
        producto = venta.producto
        if not producto.es_servicio and producto.creado_en <= PROTECTION_DATE:
            producto.stock = F('stock') + venta.cantidad
            producto.save(update_fields=['stock'])
        venta.delete()
        total += 1

    for compra in Compra.objects.filter(**nuevos).select_related('producto'):
        producto = compra.producto
        if producto and producto.creado_en <= PROTECTION_DATE:
            producto.stock = F('stock') - compra.cantidad
            producto.save(update_fields=['stock'])
        compra.delete()
        total += 1

    for gasto in Gasto.objects.filter(**nuevos):
        gasto.delete()
        total += 1

    for nombre in MODELOS_VISITANTE:
        qs = _modelo(nombre).objects.filter(**nuevos)
        if nombre == 'MovimientoContable':
            # Los asientos de regularización son del sistema, no de visitantes.
            qs = qs.exclude(descripcion__startswith='Regularización')
        borrados, _ = qs.delete()
        total += borrados
    return total


def vincular_asientos_huerfanos(empresa):
    """Enlaza ventas/compras/gastos sin `transaccion_id_contable` con su asiento.

    Los datos sembrados antes de la migración 0028 no guardaron el enlace, y sus
    asientos quedaron con la fecha del día de la siembra (no la del documento).
    Se emparejan por la descripción y el monto que genera ContabilidadService,
    se copia la fecha del documento al asiento y se guarda el enlace.
    Idempotente: solo toca documentos aún sin enlazar. Devuelve cuántos enlazó.
    """
    MovimientoContable = _modelo('MovimientoContable')
    usados = set(
        tid for nombre in ('Venta', 'Compra', 'Gasto')
        for tid in _modelo(nombre).objects.filter(empresa=empresa)
        .exclude(transaccion_id_contable__isnull=True).values_list('transaccion_id_contable', flat=True)
    )
    candidatos = {}
    for m in MovimientoContable.objects.filter(empresa=empresa).select_related('cuenta_fk').order_by('id'):
        if m.transaccion_id and m.transaccion_id not in usados and m.cuenta_fk:
            clave = (m.cuenta_fk.nombre.lower(), m.tipo, m.descripcion, m.monto.quantize(Decimal('0.01')))
            candidatos.setdefault(clave, []).append(m.transaccion_id)

    def tomar(clave):
        lista = candidatos.get(clave) or []
        while lista:
            tid = lista.pop(0)
            if tid not in usados:
                usados.add(tid)
                return tid
        return None

    enlazados = 0
    documentos = [
        ('Venta', lambda d: ('ventas', 'credito', f'Venta {d.producto.nombre} - {d.cantidad} unidades', d.monto_neto)),
        ('Compra', lambda d: ('inventario', 'debito', f'Compra {d.producto.nombre} - {d.cantidad} unidades', d.monto_neto)),
        ('Gasto', lambda d: ('gastos', 'debito', f'{d.descripcion} - {d.get_tipo_pago_display()}', d.monto)),
    ]
    for nombre, clave_de in documentos:
        Modelo = _modelo(nombre)
        qs = Modelo.objects.filter(empresa=empresa, transaccion_id_contable__isnull=True).order_by('id')
        if nombre != 'Gasto':
            qs = qs.select_related('producto')
        for doc in qs:
            cuenta, tipo, descripcion, monto = clave_de(doc)
            monto = Decimal(monto).quantize(Decimal('0.01'))
            tid = tomar((cuenta, tipo, descripcion, monto))
            if not tid and nombre == 'Gasto':
                # Formato antiguo: la descripción del gasto sin el tipo de pago.
                tid = tomar((cuenta, tipo, doc.descripcion, monto))
            if not tid:
                continue
            MovimientoContable.objects.filter(empresa=empresa, transaccion_id=tid).update(fecha=doc.fecha)
            Modelo.objects.filter(pk=doc.pk).update(transaccion_id_contable=tid)
            enlazados += 1
    return enlazados


def rejuvenecer(empresa):
    """Desplaza las fechas para que la última operación sea de ayer. Devuelve los días desplazados."""
    # Anclar en la última operación de cualquier tipo: si se anclara solo en
    # ventas, un gasto posterior quedaría con fecha futura.
    fechas = [
        _modelo(nombre).objects.filter(empresa=empresa).aggregate(m=Max('fecha'))['m']
        for nombre in ('Venta', 'Compra', 'Gasto')
    ]
    fechas = [f for f in fechas if f]
    if not fechas:
        return 0
    ultima = max(fechas)
    ayer = timezone.localdate() - timedelta(days=1)
    dias = (ayer - timezone.localtime(ultima).date()).days
    if dias <= 0:
        return 0
    delta = timedelta(days=dias)
    for nombre, campos in CAMPOS_FECHA:
        qs = _modelo(nombre).objects.filter(empresa=empresa)
        qs.update(**{campo: F(campo) + delta for campo in campos})
    return dias


class Command(BaseCommand):
    help = 'Restaura las demos: borra datos de visitantes, actualiza fechas y regulariza inventario'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Muestra lo que se haría sin modificar nada')

    def handle(self, *args, **options):
        from empresa.management.commands.regularizar_inventario import regularizar
        from empresa.models import Usuario

        dry_run = options['dry_run']
        prefijo = '[DRY RUN] ' if dry_run else ''

        for username in DEMO_USERNAMES:
            usuario = Usuario.objects.filter(username=username).select_related('empresa').first()
            if not usuario or not usuario.empresa:
                self.stdout.write(self.style.WARNING(f'  {username}: no existe o no tiene empresa, omitiendo'))
                continue
            empresa = usuario.empresa

            if dry_run:
                Venta = _modelo('Venta')
                nuevas = Venta.objects.filter(empresa=empresa, creado_en__gt=PROTECTION_DATE).count()
                self.stdout.write(f'{prefijo}{empresa.nombre}: {nuevas} ventas de visitantes por eliminar')
                continue

            with transaction.atomic():
                borrados = eliminar_datos_visitantes(empresa)
                enlazados = vincular_asientos_huerfanos(empresa)
                dias = rejuvenecer(empresa)
                _, _, ajuste = regularizar(empresa)

            self.stdout.write(self.style.SUCCESS(
                f'{empresa.nombre}: {borrados} registros de visitantes eliminados, '
                f'{enlazados} asientos enlazados, fechas desplazadas {dias} dias, '
                f'ajuste de inventario ${ajuste:,.2f}'
            ))
