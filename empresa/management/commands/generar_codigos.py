from django.core.management.base import BaseCommand
from empresa.models import CodigoInvitacion
import secrets

class Command(BaseCommand):
    help = 'Genera códigos de invitación únicos'
    
    def add_arguments(self, parser):
        parser.add_argument('cantidad', type=int, help='Cantidad de códigos a generar')
    
    def handle(self, *args, **options):
        cantidad = options['cantidad']
        codigos_generados = []
        
        for i in range(cantidad):
            codigo = f"CONTAFY-{secrets.token_urlsafe(8).upper()}"
            CodigoInvitacion.objects.create(codigo=codigo)
            codigos_generados.append(codigo)
        
        self.stdout.write(self.style.SUCCESS(f"[OK] {cantidad} códigos generados:"))
        for codigo in codigos_generados:
            self.stdout.write(f"[CODIGO] {codigo}")
        
        self.stdout.write(self.style.SUCCESS(f"\n[INFO] Envía estos códigos a tus testers junto con:"))
        self.stdout.write(f"[LINK] https://tu-app.herokuapp.com/app-beta-2024/")