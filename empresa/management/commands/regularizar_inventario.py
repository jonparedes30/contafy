"""
Management command: regularizar_inventario

Iguala el saldo contable de la cuenta "Inventario" con el valor del stock
físico (Σ stock × costo unitario) mediante un asiento de regularización.

Por qué existe: los productos creados por importación o por scripts de demo
entran con stock pero sin asiento de "Inventario inicial". Cada venta acredita
Inventario por el costo vendido y la cuenta termina en negativo, lo que
distorsiona el Balance, la liquidez y los reportes.

Asiento generado:
  - Faltante contable (stock vale más que el saldo):  Débito Inventario / Crédito Capital
    (inventario inicial no registrado = aporte en especie)
  - Sobrante contable (saldo mayor que el stock):     Débito Costo de Ventas / Crédito Inventario
    (merma o salida no registrada)

Uso:
    python manage.py regularizar_inventario --demos --dry-run
    python manage.py regularizar_inventario --empresa 10
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Sum

DEMO_USERNAMES = ['demo_comercio', 'demo_manufactura', 'demo_servicios']
# Los servicios se modelan como productos con stock "infinito"; no son inventario.
STOCK_SERVICIO = 99999


def valor_stock_fisico(empresa):
    from empresa.models import Producto
    total = Decimal('0')
    productos = Producto.objects.filter(empresa=empresa, es_servicio=False, stock__lt=STOCK_SERVICIO)
    for p in productos:
        total += Decimal(p.stock) * (p.precio_unitario or Decimal('0'))
    return total.quantize(Decimal('0.01'))


def saldo_inventario(empresa):
    from empresa.models import MovimientoContable
    movs = MovimientoContable.objects.filter(empresa=empresa, cuenta_fk__nombre__iexact='Inventario')
    debitos = movs.filter(tipo='debito').aggregate(s=Sum('monto'))['s'] or Decimal('0')
    creditos = movs.filter(tipo='credito').aggregate(s=Sum('monto'))['s'] or Decimal('0')
    return (Decimal(debitos) - Decimal(creditos)).quantize(Decimal('0.01'))


def regularizar(empresa, dry_run=False):
    """Devuelve (valor_fisico, saldo_antes, diferencia). Registra el asiento si no es dry_run."""
    from empresa.views.contabilidad import registrar_movimiento_contable

    fisico = valor_stock_fisico(empresa)
    contable = saldo_inventario(empresa)
    diferencia = fisico - contable

    if diferencia and not dry_run:
        with transaction.atomic():
            if diferencia > 0:
                registrar_movimiento_contable(
                    empresa=empresa,
                    cuenta_debito_nombre='Inventario',
                    cuenta_credito_nombre='Capital',
                    monto=diferencia,
                    descripcion='Regularización: inventario inicial no registrado',
                    tipo_cuenta_debito='activo',
                    tipo_cuenta_credito='capital',
                )
            else:
                registrar_movimiento_contable(
                    empresa=empresa,
                    cuenta_debito_nombre='Costo de Ventas',
                    cuenta_credito_nombre='Inventario',
                    monto=-diferencia,
                    descripcion='Regularización: diferencia de inventario (merma)',
                    tipo_cuenta_debito='gasto',
                    tipo_cuenta_credito='activo',
                )
    return fisico, contable, diferencia


class Command(BaseCommand):
    help = 'Iguala la cuenta Inventario con el valor del stock físico mediante un asiento de regularización'

    def add_arguments(self, parser):
        grupo = parser.add_mutually_exclusive_group(required=True)
        grupo.add_argument('--empresa', type=int, help='ID de la empresa a regularizar')
        grupo.add_argument('--demos', action='store_true', help='Regularizar las 3 empresas demo')
        parser.add_argument('--dry-run', action='store_true', help='Solo mostrar las diferencias')

    def handle(self, *args, **options):
        from empresa.models import Empresa, Usuario

        if options['demos']:
            empresas = [u.empresa for u in Usuario.objects.filter(username__in=DEMO_USERNAMES) if u.empresa]
        else:
            try:
                empresas = [Empresa.objects.get(id=options['empresa'])]
            except Empresa.DoesNotExist:
                raise CommandError(f"No existe la empresa {options['empresa']}")

        for empresa in empresas:
            fisico, contable, diferencia = regularizar(empresa, dry_run=options['dry_run'])
            estado = 'sin diferencias' if not diferencia else (
                'se registraría' if options['dry_run'] else 'regularizado'
            )
            self.stdout.write(
                f'{empresa.nombre}: stock físico ${fisico:,.2f} | Inventario contable ${contable:,.2f} '
                f'| diferencia ${diferencia:,.2f} -> {estado}'
            )
