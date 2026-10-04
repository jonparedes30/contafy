"""
Management command: reset_demos

Restaura las 3 empresas demo pre-existentes (demo_comercio, demo_manufactura,
demo_servicios) a su estado inicial eliminando las transacciones creadas por
usuarios que exploraron el sistema.

No toca datos maestros: Producto, Proveedor, Cliente, CategoriaProducto.
Solo elimina: Venta, Compra, Gasto, Capital creados DESPUÉS de PROTECTION_DATE.

PROTECTION_DATE = 2026-05-22
  → Todo lo creado antes o en esa fecha es PERMANENTE (datos de demo originales).
  → Todo lo creado después se elimina en el próximo reset.

Uso:
    python manage.py reset_demos
    python manage.py reset_demos --dry-run   (mostrar lo que se eliminaría sin borrar)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime

DEMO_USERNAMES = ['demo_comercio', 'demo_manufactura', 'demo_servicios']

# Fecha de protección fija: todo lo creado ANTES O EN esta fecha se conserva SIEMPRE.
# Representa el estado inicial de las demos en el momento de activar el auto-reset.
# NO cambiar este valor.
PROTECTION_DATE = timezone.make_aware(datetime(2026, 5, 22, 23, 59, 59))


class Command(BaseCommand):
    help = 'Resetea las transacciones de las cuentas demo a su estado inicial (auto-reset diario)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra cuántos registros se eliminarían sin borrar nada',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.NOTICE(
            f'{"[DRY RUN] " if dry_run else ""}'
            f'Reseteando demos — eliminando registros creados después de {PROTECTION_DATE} '
            f'(datos anteriores protegidos permanentemente)...'
        ))

        from empresa.models import Usuario, Venta, Compra, Gasto, Capital

        total_global = 0

        for username in DEMO_USERNAMES:
            try:
                usuario = Usuario.objects.get(username=username)
                empresa = usuario.empresa
                if not empresa:
                    self.stdout.write(self.style.WARNING(f'  {username}: sin empresa asociada, omitiendo'))
                    continue

                # Solo eliminar lo creado DESPUÉS de la fecha de protección
                ventas    = Venta.objects.filter(empresa=empresa,   fecha__gt=PROTECTION_DATE)
                compras   = Compra.objects.filter(empresa=empresa,  fecha__gt=PROTECTION_DATE)
                gastos    = Gasto.objects.filter(empresa=empresa,   fecha__gt=PROTECTION_DATE)
                capitales = Capital.objects.filter(empresa=empresa, fecha__gt=PROTECTION_DATE)

                total = ventas.count() + compras.count() + gastos.count() + capitales.count()
                total_global += total

                self.stdout.write(
                    f'  {username} ({empresa.nombre}): '
                    f'{ventas.count()} ventas, {compras.count()} compras, '
                    f'{gastos.count()} gastos, {capitales.count()} capitales -> {total} registros'
                )

                if not dry_run and total > 0:
                    ventas.delete()
                    compras.delete()
                    gastos.delete()
                    capitales.delete()
                    self.stdout.write(self.style.SUCCESS(f'    ✓ {total} registros eliminados'))
                elif not dry_run and total == 0:
                    self.stdout.write(f'    — Sin cambios (nada nuevo desde {PROTECTION_DATE})')

            except Usuario.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  {username}: usuario no encontrado, omitiendo'))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\n[DRY RUN] No se eliminó nada. '
                f'{total_global} registro(s) se eliminarían. '
                f'Ejecuta sin --dry-run para aplicar.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Reset de demos completado. {total_global} registro(s) eliminados.'
            ))
