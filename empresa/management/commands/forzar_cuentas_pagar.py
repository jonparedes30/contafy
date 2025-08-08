from django.core.management.base import BaseCommand
from empresa.models import Compra, CuentaPorPagar, Proveedor
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Fuerza la creación de cuentas por pagar para compras a crédito'

    def handle(self, *args, **options):
        compras_sin_cuenta = Compra.objects.filter(
            tipo_pago='credito'
        ).exclude(
            cuentas_por_pagar__isnull=False
        )
        
        creadas = 0
        for compra in compras_sin_cuenta:
            try:
                # Asignar proveedor existente
                if not compra.proveedor_fk:
                    # Usar el proveedor automático existente
                    proveedor = Proveedor.objects.filter(
                        empresa=compra.empresa,
                        ruc='9999999999999'
                    ).first()
                    
                    if proveedor:
                        compra.proveedor_fk = proveedor
                        compra.save(update_fields=['proveedor_fk'])
                        self.stdout.write(f'Proveedor asignado a compra #{compra.id}')
                    else:
                        self.stdout.write(f'No se encontró proveedor para compra #{compra.id}')
                
                if compra.proveedor_fk:
                    CuentaPorPagar.objects.create(
                        empresa=compra.empresa,
                        proveedor=compra.proveedor_fk,
                        compra=compra,
                        monto_original=compra.monto,
                        monto_pendiente=compra.monto,
                        fecha_vencimiento=date.today() + timedelta(days=30),
                        estado='pendiente'
                    )
                    creadas += 1
                    self.stdout.write(f'Cuenta creada para compra #{compra.id}')
                    
            except Exception as e:
                self.stdout.write(f'Error en compra #{compra.id}: {e}')
        
        self.stdout.write(self.style.SUCCESS(f'{creadas} cuentas por pagar creadas'))