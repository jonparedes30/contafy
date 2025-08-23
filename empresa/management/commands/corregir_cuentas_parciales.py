from django.core.management.base import BaseCommand
from empresa.models import CuentaPorCobrar, CuentaPorPagar, PagoCuentaPorCobrar, PagoCuentaPorPagar
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Corrige los montos pendientes de cuentas con pagos parciales'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando corrección de cuentas con pagos parciales...')
        
        # Corregir cuentas por cobrar
        cuentas_cobrar = CuentaPorCobrar.objects.all()
        corregidas_cobrar = 0
        
        for cuenta in cuentas_cobrar:
            # Calcular total de pagos realizados
            total_pagos = cuenta.pagos.aggregate(total=Sum('monto_pagado'))['total'] or 0
            
            # Calcular monto pendiente correcto
            monto_pendiente_correcto = cuenta.monto_original - total_pagos
            
            # Si hay diferencia, corregir
            if cuenta.monto_pendiente != monto_pendiente_correcto:
                self.stdout.write(f'Corrigiendo cuenta por cobrar ID {cuenta.id}: {cuenta.monto_pendiente} -> {monto_pendiente_correcto}')
                cuenta.monto_pendiente = max(0, monto_pendiente_correcto)
                
                # Actualizar estado
                if cuenta.monto_pendiente <= 0:
                    cuenta.estado = 'pagada'
                elif cuenta.estado == 'pagada' and cuenta.monto_pendiente > 0:
                    cuenta.estado = 'pendiente'
                
                cuenta.save()
                corregidas_cobrar += 1
        
        # Corregir cuentas por pagar
        cuentas_pagar = CuentaPorPagar.objects.all()
        corregidas_pagar = 0
        
        for cuenta in cuentas_pagar:
            # Calcular total de pagos realizados
            total_pagos = cuenta.pagos.aggregate(total=Sum('monto_pagado'))['total'] or 0
            
            # Calcular monto pendiente correcto
            monto_pendiente_correcto = cuenta.monto_original - total_pagos
            
            # Si hay diferencia, corregir
            if cuenta.monto_pendiente != monto_pendiente_correcto:
                self.stdout.write(f'Corrigiendo cuenta por pagar ID {cuenta.id}: {cuenta.monto_pendiente} -> {monto_pendiente_correcto}')
                cuenta.monto_pendiente = max(0, monto_pendiente_correcto)
                
                # Actualizar estado
                if cuenta.monto_pendiente <= 0:
                    cuenta.estado = 'pagada'
                elif cuenta.estado == 'pagada' and cuenta.monto_pendiente > 0:
                    cuenta.estado = 'pendiente'
                
                cuenta.save()
                corregidas_pagar += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Corrección completada: {corregidas_cobrar} cuentas por cobrar y {corregidas_pagar} cuentas por pagar corregidas'
            )
        )