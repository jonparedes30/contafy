"""
Management command: reset_demos

Restaura las 3 empresas demo pre-existentes (demo_comercio, demo_manufactura,
demo_servicios) a su estado inicial eliminando las transacciones creadas por
usuarios que exploraron el sistema.

No toca datos maestros: Producto, Proveedor, Cliente, CategoriaProducto.
Solo elimina: Venta, Compra, Gasto, Capital creados después de RESET_DATE.

Uso:
    python manage.py reset_demos
    python manage.py reset_demos --dry-run   (mostrar lo que se eliminaría sin borrar)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

DEMO_USERNAMES = ['demo_comercio', 'demo_manufactura', 'demo_servicios']
# Mantener datos creados por el comando crear_demos (hasta 90 días atrás)
CUTOFF_DAYS = 90


class Command(BaseCommand):
    help = 'Resetea las transacciones de las cuentas demo a su estado inicial'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra cuántos registros se eliminarían sin borrar nada',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        cutoff = timezone.now() - timedelta(days=CUTOFF_DAYS)

        self.stdout.write(self.style.NOTICE(
            f'{"[DRY RUN] " if dry_run else ""}Reseteando demos (eliminando registros creados después de {cutoff.date()})...'
        ))

        from empresa.models import Usuario, Venta, Compra, Gasto, Capital

        for username in DEMO_USERNAMES:
            try:
                usuario = Usuario.objects.get(username=username)
                empresa = usuario.empresa
                if not empresa:
                    self.stdout.write(self.style.WARNING(f'  {username}: sin empresa asociada, omitiendo'))
                    continue

                ventas   = Venta.objects.filter(empresa=empresa,   fecha__gt=cutoff.date())
                compras  = Compra.objects.filter(empresa=empresa,  fecha__gt=cutoff.date())
                gastos   = Gasto.objects.filter(empresa=empresa,   fecha__gt=cutoff.date())
                capitales = Capital.objects.filter(empresa=empresa, fecha__gt=cutoff.date())

                total = ventas.count() + compras.count() + gastos.count() + capitales.count()
                self.stdout.write(
                    f'  {username} ({empresa.nombre}): '
                    f'{ventas.count()} ventas, {compras.count()} compras, '
                    f'{gastos.count()} gastos, {capitales.count()} capitales → {total} registros'
                )

                if not dry_run and total > 0:
                    ventas.delete()
                    compras.delete()
                    gastos.delete()
                    capitales.delete()
                    self.stdout.write(self.style.SUCCESS(f'    ✓ {total} registros eliminados'))

            except Usuario.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  {username}: usuario no encontrado, omitiendo'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No se eliminó nada. Ejecuta sin --dry-run para aplicar.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Reset de demos completado.'))
