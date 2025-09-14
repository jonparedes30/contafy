from django.core.management.base import BaseCommand
from empresa.models import Empresa
from empresa.services.cuentas_default_service import CuentasDefaultService

class Command(BaseCommand):
    help = 'Crea cuentas contables por defecto para empresas existentes que no las tengan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID específico de empresa para crear cuentas',
        )
        parser.add_argument(
            '--todas',
            action='store_true',
            help='Crear cuentas para todas las empresas que no las tengan',
        )

    def handle(self, *args, **options):
        if options['empresa_id']:
            try:
                empresa = Empresa.objects.get(id=options['empresa_id'])
                cuentas_creadas = CuentasDefaultService.crear_cuentas_default(empresa)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Creadas {len(cuentas_creadas)} cuentas para {empresa.nombre}'
                    )
                )
            except Empresa.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Empresa con ID {options["empresa_id"]} no encontrada')
                )
        
        elif options['todas']:
            empresas = Empresa.objects.all()
            total_cuentas = 0
            
            for empresa in empresas:
                cuentas_creadas = CuentasDefaultService.crear_cuentas_default(empresa)
                total_cuentas += len(cuentas_creadas)
                if cuentas_creadas:
                    self.stdout.write(
                        f'✅ {empresa.nombre}: {len(cuentas_creadas)} cuentas creadas'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Proceso completado. Total: {total_cuentas} cuentas creadas'
                )
            )
        
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Usa --empresa-id <ID> para una empresa específica o --todas para todas las empresas'
                )
            )