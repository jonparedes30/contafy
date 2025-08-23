from django.core.management.base import BaseCommand
from empresa.models import CuentaPorCobrar, Venta

class Command(BaseCommand):
    help = 'Debug cuentas por cobrar'

    def handle(self, *args, **options):
        self.stdout.write('=== TODAS LAS CUENTAS POR COBRAR ===')
        for cuenta in CuentaPorCobrar.objects.all():
            self.stdout.write(f'ID: {cuenta.id}')
            self.stdout.write(f'Cliente: {cuenta.cliente.nombre}')
            self.stdout.write(f'Monto Original: {cuenta.monto_original}')
            self.stdout.write(f'Monto Pendiente: {cuenta.monto_pendiente}')
            self.stdout.write(f'Estado: {cuenta.estado}')
            self.stdout.write(f'Empresa: {cuenta.empresa.nombre}')
            self.stdout.write('---')
        
        self.stdout.write('\n=== VENTAS A CRÉDITO RECIENTES ===')
        for venta in Venta.objects.filter(tipo_pago='credito').order_by('-fecha')[:5]:
            self.stdout.write(f'Venta ID: {venta.id}')
            self.stdout.write(f'Cliente: {venta.cliente_display}')
            self.stdout.write(f'Monto: {venta.monto}')
            self.stdout.write(f'Fecha: {venta.fecha}')
            self.stdout.write(f'Empresa: {venta.empresa.nombre}')
            
            # Verificar si tiene cuenta por cobrar
            cuenta = CuentaPorCobrar.objects.filter(venta=venta).first()
            if cuenta:
                self.stdout.write(f'Tiene cuenta por cobrar: Sí (ID: {cuenta.id})')
            else:
                self.stdout.write(f'Tiene cuenta por cobrar: NO')
            self.stdout.write('---')