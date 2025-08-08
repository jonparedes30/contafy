from django.core.management.base import BaseCommand
from empresa.models import Compra, CuentaPorPagar

class Command(BaseCommand):
    help = 'Verifica compras a crédito y sus cuentas por pagar'

    def handle(self, *args, **options):
        compras_credito = Compra.objects.filter(tipo_pago='credito').order_by('-id')[:10]
        
        self.stdout.write(f'Últimas 10 compras a crédito:')
        for compra in compras_credito:
            cuentas = CuentaPorPagar.objects.filter(compra=compra)
            self.stdout.write(f'Compra #{compra.id} - {compra.proveedor_display} - ${compra.monto} - Cuentas: {cuentas.count()}')
            
        total_cuentas = CuentaPorPagar.objects.count()
        self.stdout.write(f'Total cuentas por pagar: {total_cuentas}')