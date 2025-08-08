from django.core.management.base import BaseCommand
from empresa.services.metas_service import ServicioMetas
from empresa.models import Empresa

class Command(BaseCommand):
    help = 'Actualiza el historial de todas las metas activas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID de la empresa específica (opcional)',
        )
        parser.add_argument(
            '--generar-alertas',
            action='store_true',
            help='Generar alertas automáticas después de actualizar',
        )

    def handle(self, *args, **options):
        empresa_id = options.get('empresa_id')
        generar_alertas = options.get('generar_alertas')
        
        # Obtener empresas a procesar
        if empresa_id:
            empresas = Empresa.objects.filter(id=empresa_id)
        else:
            empresas = Empresa.objects.all()
        
        if not empresas.exists():
            self.stdout.write(self.style.ERROR('No se encontraron empresas para procesar'))
            return
        
        total_metas_actualizadas = 0
        
        for empresa in empresas:
            self.stdout.write(f'Procesando empresa: {empresa.nombre}')
            
            # Actualizar historial de metas
            metas_empresa = empresa.metafinanciera_set.all()
            for meta in metas_empresa:
                try:
                    meta.actualizar_historial()
                    total_metas_actualizadas += 1
                    self.stdout.write(f'  ✓ Meta {meta.get_tipo_display()} ({meta.mes}/{meta.anio}) actualizada')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error actualizando meta {meta.get_tipo_display()}: {str(e)}')
                    )
        
        # Generar alertas si se solicita
        if generar_alertas:
            self.stdout.write('Generando alertas automáticas...')
            try:
                ServicioMetas.generar_alertas_automaticas()
                self.stdout.write(self.style.SUCCESS('Alertas generadas exitosamente'))
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error generando alertas: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso completado. {total_metas_actualizadas} metas actualizadas.'
            )
        ) 