from django.core.management.base import BaseCommand
from empresa.models import Venta, CuentaPorCobrar, Cliente
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Crea cuentas por cobrar faltantes para ventas a crédito'

    def handle(self, *args, **options):
        self.stdout.write('Buscando ventas a crédito sin cuenta por cobrar...')
        
        # Buscar ventas a crédito sin cuenta por cobrar
        ventas_sin_cuenta = []
        for venta in Venta.objects.filter(tipo_pago='credito'):
            if not CuentaPorCobrar.objects.filter(venta=venta).exists():
                ventas_sin_cuenta.append(venta)
        
        self.stdout.write(f'Encontradas {len(ventas_sin_cuenta)} ventas sin cuenta por cobrar')
        
        creadas = 0
        for venta in ventas_sin_cuenta:
            try:
                # Asegurar que tenga cliente
                if not venta.cliente_fk:
                    nombre_cliente = venta.cliente_nombre or 'Cliente General'
                    cliente, created = Cliente.objects.get_or_create(
                        empresa=venta.empresa,
                        nombre=nombre_cliente,
                        defaults={
                            'numero_documento': '9999999999',
                            'limite_credito': 1000
                        }
                    )
                    venta.cliente_fk = cliente
                    venta.save()
                
                # Crear cuenta por cobrar
                CuentaPorCobrar.objects.create(
                    empresa=venta.empresa,
                    cliente=venta.cliente_fk,
                    venta=venta,
                    monto_original=venta.monto,
                    monto_pendiente=venta.monto,
                    fecha_vencimiento=date.today() + timedelta(days=30),
                    estado='pendiente'
                )
                
                self.stdout.write(f'Creada cuenta para venta ID {venta.id} - Cliente: {venta.cliente_display} - Monto: ${venta.monto}')
                creadas += 1
                
            except Exception as e:
                self.stdout.write(f'Error creando cuenta para venta ID {venta.id}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Proceso completado: {creadas} cuentas por cobrar creadas')
        )