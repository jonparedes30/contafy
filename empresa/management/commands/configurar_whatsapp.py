"""
Comando para configurar WhatsApp en las empresas
"""
from django.core.management.base import BaseCommand
from empresa.models import Empresa

class Command(BaseCommand):
    help = 'Configura números de WhatsApp para las empresas'

    def add_arguments(self, parser):
        parser.add_argument('--empresa-id', type=int, help='ID de la empresa')
        parser.add_argument('--telefono', type=str, help='Número de WhatsApp (+593987654321)')

    def handle(self, *args, **options):
        if options['empresa_id'] and options['telefono']:
            try:
                empresa = Empresa.objects.get(id=options['empresa_id'])
                empresa.telefono_whatsapp = options['telefono']
                empresa.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'WhatsApp configurado para {empresa.nombre}: {options["telefono"]}'
                    )
                )
            except Empresa.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Empresa con ID {options["empresa_id"]} no encontrada')
                )
        else:
            # Mostrar empresas sin WhatsApp configurado
            empresas_sin_whatsapp = Empresa.objects.filter(telefono_whatsapp='')
            
            self.stdout.write('Empresas sin WhatsApp configurado:')
            for empresa in empresas_sin_whatsapp:
                self.stdout.write(f'ID: {empresa.id} - {empresa.nombre}')
            
            self.stdout.write('\nUso: python manage.py configurar_whatsapp --empresa-id 1 --telefono +593987654321')