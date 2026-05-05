import json
from django.core.management.base import BaseCommand, CommandError
from empresa.models import Producto
from core.pos_identifier import identify_products, dumps_json


class Command(BaseCommand):
    help = 'Probar el detector POS con payload JSON: logos, ocr, barcodes. Lee payload desde argumento o stdin.'

    def add_arguments(self, parser):
        parser.add_argument('--payload', type=str, help='JSON payload inline')
        parser.add_argument('--modo', choices=['single', 'multi'], default='single')
        parser.add_argument('--context', choices=['venta','inventario'], default='venta', help='Contexto de uso: venta o inventario')
        parser.add_argument('--empresa', type=int, help='ID de la empresa (filtra productos)')

    def handle(self, *args, **options):
        raw = options.get('payload')
        if not raw:
            # read from stdin
            self.stdout.write('Esperando payload JSON por stdin... (Ctrl-D para terminar)')
            raw = ''.join(self.stdin)

        try:
            payload = json.loads(raw)
        except Exception as e:
            raise CommandError(f'Payload JSON inválido: {e}')

        empresa_id = options.get('empresa')
        qs = Producto.objects.all()
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        products_db = []
        for p in qs[:500]:
            products_db.append(
                {
                    'id': p.id,
                    'nombre': p.nombre,
                    'marca': getattr(p, 'marca', '') or '',
                    'presentacion': p.descripcion or '',
                    'barcode': p.codigo_barras or '',
                    'sku': p.codigo or '',
                }
            )

        # Allow tester to choose context: venta|inventario
        context = options.get('context') or 'venta'
        result = identify_products(payload, products_db, modo=options.get('modo'), context=context)
        self.stdout.write(dumps_json(result))
