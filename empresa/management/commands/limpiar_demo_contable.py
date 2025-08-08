from django.core.management.base import BaseCommand
from empresa.models import Venta, Compra, Gasto, MovimientoContable, Producto

class Command(BaseCommand):
    help = 'Elimina todos los datos demo generados para pruebas (ventas, compras, gastos, movimientos contables y producto demo)'

    def handle(self, *args, **options):
        # Eliminar movimientos contables demo
        movs = MovimientoContable.objects.filter(descripcion__icontains='demo')
        n_movs = movs.count()
        movs.delete()
        # Eliminar ventas demo
        ventas = Venta.objects.filter(producto__codigo='DEMO-001')
        n_ventas = ventas.count()
        ventas.delete()
        # Eliminar compras demo
        compras = Compra.objects.filter(producto__codigo='DEMO-001')
        n_compras = compras.count()
        compras.delete()
        # Eliminar gastos demo
        gastos = Gasto.objects.filter(descripcion__icontains='demo')
        n_gastos = gastos.count()
        gastos.delete()
        # Eliminar producto demo
        productos = Producto.objects.filter(codigo='DEMO-001')
        n_productos = productos.count()
        productos.delete()
        self.stdout.write(self.style.SUCCESS(f"Movimientos demo eliminados: {n_movs}"))
        self.stdout.write(self.style.SUCCESS(f"Ventas demo eliminadas: {n_ventas}"))
        self.stdout.write(self.style.SUCCESS(f"Compras demo eliminadas: {n_compras}"))
        self.stdout.write(self.style.SUCCESS(f"Gastos demo eliminados: {n_gastos}"))
        self.stdout.write(self.style.SUCCESS(f"Productos demo eliminados: {n_productos}"))
        self.stdout.write(self.style.SUCCESS("Limpieza de datos demo completada.")) 