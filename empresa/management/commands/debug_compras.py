from django.core.management.base import BaseCommand
from empresa.models import Compra

class Command(BaseCommand):
    def handle(self, *args, **options):
        compras = Compra.objects.filter(tipo_pago='credito').order_by('-id')[:5]
        
        for compra in compras:
            self.stdout.write(f'Compra #{compra.id}:')
            self.stdout.write(f'  - proveedor_fk: {compra.proveedor_fk}')
            self.stdout.write(f'  - proveedor_nombre: {compra.proveedor_nombre}')
            self.stdout.write(f'  - tipo_pago: {compra.tipo_pago}')
            self.stdout.write('---')