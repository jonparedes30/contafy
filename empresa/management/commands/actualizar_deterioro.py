from django.core.management.base import BaseCommand
from empresa.models import CuentaPorCobrar

class Command(BaseCommand):
    help = 'Actualiza el deterioro de cuentas por cobrar según NIIF 9'

    def handle(self, *args, **options):
        cuentas = CuentaPorCobrar.objects.filter(estado='pendiente')
        actualizadas = 0
        
        for cuenta in cuentas:
            deterioro_anterior = cuenta.deterioro_esperado
            cuenta.actualizar_deterioro()
            
            if cuenta.deterioro_esperado != deterioro_anterior:
                actualizadas += 1
                self.stdout.write(
                    f'Actualizada cuenta {cuenta.cliente.nombre}: '
                    f'${deterioro_anterior} -> ${cuenta.deterioro_esperado}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Se actualizaron {actualizadas} cuentas por cobrar')
        )