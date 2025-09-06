from django.core.management.base import BaseCommand
from empresa.models import Empresa
from empresa.services.niif_service import NIIFService

class Command(BaseCommand):
    help = 'Ejecuta cierre contable según NIIF para todas las empresas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=str,
            help='RUC de empresa específica para procesar'
        )

    def handle(self, *args, **options):
        if options['empresa']:
            try:
                empresa = Empresa.objects.get(ruc=options['empresa'])
                empresas = [empresa]
            except Empresa.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Empresa con RUC {options["empresa"]} no encontrada')
                )
                return
        else:
            empresas = Empresa.objects.all()

        total_procesadas = 0
        
        for empresa in empresas:
            try:
                resultados = NIIFService.ejecutar_cierre_niif(empresa)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {empresa.nombre}: '
                        f'Deterioro: {resultados["deterioro_actualizado"]} cuentas, '
                        f'Ingresos: ${resultados["ingresos_reconocidos"]}, '
                        f'Instrumentos: ${resultados["instrumentos_evaluados"]}'
                    )
                )
                total_procesadas += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error en {empresa.nombre}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Cierre NIIF completado para {total_procesadas} empresas')
        )