from django.core.management.base import BaseCommand
from empresa.models import CodigoInvitacion
import random
import string

class Command(BaseCommand):
    help = 'Crear códigos de invitación nuevos'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=10, help='Cantidad de códigos a crear')

    def handle(self, *args, **options):
        cantidad = options['cantidad']
        
        for i in range(cantidad):
            # Generar código único
            while True:
                codigo = 'CONTAFY-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not CodigoInvitacion.objects.filter(codigo=codigo).exists():
                    break
            
            CodigoInvitacion.objects.create(codigo=codigo)
            self.stdout.write(f"[OK] Código creado: {codigo}")
        
        self.stdout.write(f"\n{cantidad} códigos creados exitosamente")
        
        # Mostrar códigos disponibles
        disponibles = CodigoInvitacion.objects.filter(usado=False)
        self.stdout.write(f"\nCódigos disponibles: {disponibles.count()}")
        for codigo in disponibles[:10]:
            self.stdout.write(f"- {codigo.codigo}")