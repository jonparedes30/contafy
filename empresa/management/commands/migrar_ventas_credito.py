from django.core.management.base import BaseCommand
from empresa.models import Venta, CuentaPorCobrar, Cliente
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Migra ventas a crédito existentes para crear cuentas por cobrar'

    def handle(self, *args, **options):
        # Buscar ventas a crédito que no tienen cuenta por cobrar
        ventas_credito = Venta.objects.filter(
            tipo_pago='credito'
        ).exclude(
            cuentas_por_cobrar__isnull=False
        )
        
        creadas = 0
        errores = 0
        
        for venta in ventas_credito:
            try:
                # Crear cliente si no existe
                if not venta.cliente_fk and venta.cliente_nombre:
                    # Buscar cliente existente por nombre
                    cliente = Cliente.objects.filter(
                        empresa=venta.empresa,
                        nombre=venta.cliente_nombre
                    ).first()
                    
                    if not cliente:
                        # Crear cliente con documento único
                        import random
                        documento = f'999{random.randint(1000000, 9999999)}'
                        cliente = Cliente.objects.create(
                            empresa=venta.empresa,
                            nombre=venta.cliente_nombre,
                            numero_documento=documento,
                            limite_credito=1000
                        )
                    
                    venta.cliente_fk = cliente
                    venta.save(update_fields=['cliente_fk'])
                
                # Crear cuenta por cobrar si hay cliente
                if venta.cliente_fk:
                    CuentaPorCobrar.objects.create(
                        empresa=venta.empresa,
                        cliente=venta.cliente_fk,
                        venta=venta,
                        monto_original=venta.monto,
                        monto_pendiente=venta.monto,
                        fecha_vencimiento=date.today() + timedelta(days=30),
                        estado='pendiente'
                    )
                    creadas += 1
                    self.stdout.write(f'[OK] Cuenta por cobrar creada para venta #{venta.id}')
                
            except Exception as e:
                errores += 1
                self.stdout.write(f'[ERROR] Error en venta #{venta.id}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Migración completada: {creadas} cuentas creadas, {errores} errores')
        )