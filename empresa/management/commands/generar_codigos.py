from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from empresa.models import CodigoInvitacion
import secrets

class Command(BaseCommand):
    help = 'Genera códigos de invitación únicos'
    
    def add_arguments(self, parser):
        parser.add_argument('cantidad', type=int, help='Cantidad de códigos a generar')
    
    def handle(self, *args, **options):
        cantidad = options['cantidad']
        codigos_generados = []
        vistos = set()
        
        for _ in range(cantidad):
            for intento in range(10):
                base = secrets.token_urlsafe(8).upper()
                codigo = f"CONTAFY-{base}"
                
                if codigo in vistos:
                    continue
                
                try:
                    with transaction.atomic():
                        obj = CodigoInvitacion.objects.create(codigo=codigo)
                    codigos_generados.append(obj.codigo)
                    vistos.add(obj.codigo)
                    break
                except IntegrityError:
                    continue
            else:
                raise RuntimeError("No se pudo generar un código único tras múltiples intentos.")
        
        self.stdout.write(self.style.SUCCESS(f"[OK] {cantidad} códigos generados:"))
        for codigo in codigos_generados:
            self.stdout.write(f"[CODIGO] {codigo}")
        
        self.stdout.write(self.style.SUCCESS(f"\n[INFO] Envía estos códigos a tus testers junto con:"))
        self.stdout.write(f"[LINK] https://contafy-pruebas-30fdb804cc25.herokuapp.com/app-beta-2024/")