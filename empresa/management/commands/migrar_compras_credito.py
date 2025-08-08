from django.core.management.base import BaseCommand
from empresa.models import Compra, CuentaPorPagar, Proveedor
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Migra compras a crédito existentes para crear cuentas por pagar'

    def handle(self, *args, **options):
        # Buscar compras a crédito que no tienen cuenta por pagar
        compras_credito = Compra.objects.filter(
            tipo_pago='credito'
        ).exclude(
            cuentas_por_pagar__isnull=False
        )
        
        creadas = 0
        errores = 0
        
        for compra in compras_credito:
            try:
                # Crear proveedor si no existe
                if not compra.proveedor_fk and compra.proveedor_nombre:
                    proveedor, created = Proveedor.objects.get_or_create(
                        empresa=compra.empresa,
                        nombre=compra.proveedor_nombre,
                        defaults={
                            'ruc': '9999999999999',
                            'dias_credito': 30
                        }
                    )
                    compra.proveedor_fk = proveedor
                    compra.save(update_fields=['proveedor_fk'])
                
                # Crear cuenta por pagar si hay proveedor
                if compra.proveedor_fk:
                    CuentaPorPagar.objects.create(
                        empresa=compra.empresa,
                        proveedor=compra.proveedor_fk,
                        compra=compra,
                        monto_original=compra.monto,
                        monto_pendiente=compra.monto,
                        fecha_vencimiento=date.today() + timedelta(days=compra.proveedor_fk.dias_credito or 30),
                        estado='pendiente'
                    )
                    creadas += 1
                    self.stdout.write(f'[OK] Cuenta por pagar creada para compra #{compra.id}')
                
            except Exception as e:
                errores += 1
                self.stdout.write(f'[ERROR] Error en compra #{compra.id}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Migración completada: {creadas} cuentas creadas, {errores} errores')
        )