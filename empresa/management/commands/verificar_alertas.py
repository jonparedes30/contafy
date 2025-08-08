"""
Comando para verificar y enviar alertas automáticamente
Ejecutar con: python manage.py verificar_alertas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from empresa.models import MetaFinanciera, Producto, Empresa
from empresa.services.notificaciones_service import NotificacionesService
from empresa.services.benchmarking_avanzado_service import BenchmarkingAvanzadoService

class Command(BaseCommand):
    help = 'Verifica y envía alertas automáticas por email y WhatsApp'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando verificación de alertas...')
        
        # Verificar metas críticas
        self.verificar_metas_criticas()
        
        # Verificar metas cumplidas
        self.verificar_metas_cumplidas()
        
        # Verificar stock bajo
        self.verificar_stock_bajo()
        
        # Verificar alertas predictivas
        self.verificar_alertas_predictivas()
        
        self.stdout.write(self.style.SUCCESS('Verificación de alertas completada'))
    
    def verificar_metas_criticas(self):
        """Verifica metas en estado crítico"""
        hoy = datetime.now()
        metas_criticas = MetaFinanciera.objects.filter(
            mes=hoy.month,
            anio=hoy.year,
            alertas_activas=True
        )
        
        for meta in metas_criticas:
            if meta.estado == 'crítica':
                # Verificar si ya se envió alerta hoy
                from empresa.models import AlertaMeta
                alerta_hoy = AlertaMeta.objects.filter(
                    meta=meta,
                    tipo='crítica',
                    fecha_creacion__date=hoy.date()
                ).exists()
                
                if not alerta_hoy:
                    NotificacionesService.notificar_meta_critica(meta)
                    
                    # Crear registro de alerta
                    AlertaMeta.objects.create(
                        meta=meta,
                        tipo='crítica',
                        mensaje=f'Meta {meta.get_tipo_display()} en estado crítico: {meta.progreso_actual:.1f}%',
                        enviada=True,
                        fecha_envio=timezone.now()
                    )
                    
                    self.stdout.write(f'Alerta crítica enviada: {meta}')
    
    def verificar_metas_cumplidas(self):
        """Verifica metas recién cumplidas"""
        hoy = datetime.now()
        metas_cumplidas = MetaFinanciera.objects.filter(
            mes=hoy.month,
            anio=hoy.year,
            alertas_activas=True
        )
        
        for meta in metas_cumplidas:
            if meta.estado == 'completada':
                # Verificar si ya se envió felicitación
                from empresa.models import AlertaMeta
                felicitacion_enviada = AlertaMeta.objects.filter(
                    meta=meta,
                    tipo='felicitación',
                    fecha_creacion__date=hoy.date()
                ).exists()
                
                if not felicitacion_enviada:
                    NotificacionesService.notificar_meta_cumplida(meta)
                    
                    # Crear registro de felicitación
                    AlertaMeta.objects.create(
                        meta=meta,
                        tipo='felicitación',
                        mensaje=f'¡Meta {meta.get_tipo_display()} cumplida! {meta.progreso_actual:.1f}%',
                        enviada=True,
                        fecha_envio=timezone.now()
                    )
                    
                    self.stdout.write(f'Felicitación enviada: {meta}')
    
    def verificar_stock_bajo(self):
        """Verifica productos con stock bajo"""
        from django.db import models
        productos_stock_bajo = Producto.objects.filter(
            stock__lte=models.F('stock_minimo')
        )
        
        for producto in productos_stock_bajo:
            # Verificar si ya se envió alerta esta semana
            from datetime import timedelta
            hace_una_semana = timezone.now() - timedelta(days=7)
            
            # Aquí podrías crear un modelo para trackear alertas de stock
            # Por simplicidad, enviamos la alerta
            NotificacionesService.notificar_stock_bajo(producto)
            self.stdout.write(f'Alerta stock bajo enviada: {producto}')
    
    def verificar_alertas_predictivas(self):
        """Verifica alertas del análisis predictivo"""
        empresas_activas = Empresa.objects.all()
        
        for empresa in empresas_activas:
            try:
                benchmarking = BenchmarkingAvanzadoService.obtener_benchmarking_completo_avanzado(empresa)
                alertas = benchmarking.get('analisis_predictivo', {}).get('alertas_tempranas', [])
                
                for alerta in alertas:
                    if alerta['tipo'] == 'critico':
                        NotificacionesService.notificar_alerta_predictiva(empresa, alerta)
                        self.stdout.write(f'Alerta predictiva enviada: {empresa.nombre}')
                        
            except Exception as e:
                self.stdout.write(f'Error procesando {empresa.nombre}: {e}')