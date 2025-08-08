"""
Servicio para gestión avanzada de metas financieras.
Incluye alertas automáticas, notificaciones y benchmarking sectorial.
"""
from django.utils import timezone
from django.db.models import Avg, Count, Sum
from datetime import datetime, timedelta
from calendar import monthrange
from empresa.models import (
    MetaFinanciera, HistorialMeta, AlertaMeta, 
    NotificacionMeta, BenchmarkingSectorial,
    Venta, Gasto, Compra, Empresa, CuentaContable, MovimientoContable
)

class ServicioMetas:
    """Servicio principal para gestión de metas"""
    
    @staticmethod
    def actualizar_historial_metas(empresa=None):
        """Actualiza el historial de todas las metas activas"""
        metas = MetaFinanciera.objects.filter(
            empresa=empresa
        ) if empresa else MetaFinanciera.objects.all()
        
        for meta in metas:
            meta.actualizar_historial()
    
    @staticmethod
    def generar_alertas_automaticas():
        """Genera notificaciones automáticas solo para eventos importantes"""
        hoy = timezone.now()
        metas_activas = MetaFinanciera.objects.filter(
            alertas_activas=True,
            mes=hoy.month,
            anio=hoy.year
        )
        
        for meta in metas_activas:
            ServicioMetas._verificar_y_crear_alerta(meta)
    
    @staticmethod
    def _verificar_y_crear_alerta(meta):
        """Verifica el estado de una meta y crea notificaciones solo para eventos importantes"""
        progreso = meta.progreso_actual
        dias_restantes = meta.dias_restantes_mes()
        
        # Verificar si ya existe una notificación reciente (últimas 24 horas)
        notificacion_reciente = NotificacionMeta.objects.filter(
            empresa=meta.empresa,
            titulo__icontains=f"Meta: {meta.get_tipo_display()}",
            fecha_creacion__gte=timezone.now() - timedelta(days=1)
        ).exists()
        
        if notificacion_reciente:
            return
        
        # Crear notificaciones solo para eventos importantes
        if progreso >= 100:
            ServicioMetas._crear_notificacion(meta, 'success', 
                f"¡Felicitaciones! Has superado tu meta de {meta.get_tipo_display()} en un {progreso:.1f}%")
        
        elif progreso < 25 and dias_restantes < 7:
            ServicioMetas._crear_notificacion(meta, 'danger',
                f"¡Atención crítica! Tu meta de {meta.get_tipo_display()} está en estado crítico ({progreso:.1f}%). Solo quedan {dias_restantes} días.")
    
    @staticmethod
    def _crear_notificacion(meta, tipo, mensaje):
        """Crea una notificación para una meta (solo eventos importantes)"""
        NotificacionMeta.objects.create(
            empresa=meta.empresa,
            titulo=f"Meta: {meta.get_tipo_display()}",
            mensaje=mensaje,
            tipo=tipo,
            accion_url='empresa:gestionar_metas'
        )
        
    @staticmethod
    def generar_recomendaciones_metas(empresa):
        """Genera recomendaciones personalizadas para las metas de una empresa"""
        metas_activas = MetaFinanciera.objects.filter(
            empresa=empresa,
            mes=timezone.now().month,
            anio=timezone.now().year
        )
        
        recomendaciones = []
        for meta in metas_activas:
            recomendacion = meta.generar_recomendacion()
            recomendaciones.append({
                'meta': meta,
                'recomendacion': recomendacion,
                'progreso': meta.progreso_actual,
                'estado': meta.estado
            })
        
        return recomendaciones
    
    @staticmethod
    def calcular_benchmarking_sectorial(empresa):
        """Calcula benchmarking sectorial avanzado con valuación y análisis predictivo"""
        from empresa.services.benchmarking_avanzado_service import BenchmarkingAvanzadoService
        return BenchmarkingAvanzadoService.obtener_benchmarking_completo_avanzado(empresa)
    
    @staticmethod
    def generar_metas_dinamicas(empresa):
        """Genera sugerencias de metas dinámicas basadas en el rendimiento histórico"""
        # Obtener rendimiento histórico de los últimos 6 meses
        meses_atras = 6
        rendimiento_historico = []
        
        for i in range(meses_atras):
            fecha = timezone.now() - timedelta(days=30*i)
            ventas_mes = Venta.objects.filter(
                empresa=empresa,
                fecha__month=fecha.month,
                fecha__year=fecha.year
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            gastos_mes = Gasto.objects.filter(
                empresa=empresa,
                fecha__month=fecha.month,
                fecha__year=fecha.year
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            rendimiento_historico.append({
                'mes': fecha.month,
                'anio': fecha.year,
                'ventas': ventas_mes,
                'gastos': gastos_mes,
                'utilidad': ventas_mes - gastos_mes
            })
        
        # Calcular tendencias
        from decimal import Decimal
        ventas_promedio = sum(Decimal(str(r['ventas'])) for r in rendimiento_historico) / len(rendimiento_historico)
        utilidad_promedio = sum(Decimal(str(r['utilidad'])) for r in rendimiento_historico) / len(rendimiento_historico)
        
        # Calcular crecimiento
        if len(rendimiento_historico) >= 2:
            crecimiento_ventas = ((Decimal(str(rendimiento_historico[0]['ventas'])) - Decimal(str(rendimiento_historico[1]['ventas']))) / 
                                 Decimal(str(rendimiento_historico[1]['ventas'])) * 100) if rendimiento_historico[1]['ventas'] > 0 else 0
        else:
            crecimiento_ventas = 0
        
        # Generar sugerencias
        gastos_promedio = sum(Decimal(str(r['gastos'])) for r in rendimiento_historico) / len(rendimiento_historico)
        sugerencias = {
            'ventas': {
                'conservadora': ventas_promedio * Decimal('1.05'),  # 5% de crecimiento
                'moderada': ventas_promedio * Decimal('1.10'),      # 10% de crecimiento
                'ambiciosa': ventas_promedio * Decimal('1.20')      # 20% de crecimiento
            },
            'gastos': {
                'conservadora': gastos_promedio * Decimal('1.05'),   # 5% de crecimiento
                'moderada': gastos_promedio * Decimal('1.15'),      # 15% de crecimiento
                'ambiciosa': gastos_promedio * Decimal('1.25')      # 25% de crecimiento
            },
            'utilidad': {
                'conservadora': utilidad_promedio * Decimal('1.05'),
                'moderada': utilidad_promedio * Decimal('1.15'),
                'ambiciosa': utilidad_promedio * Decimal('1.25')
            },
            'tendencia': {
                'crecimiento_ventas': float(crecimiento_ventas),
                'recomendacion': 'incrementar' if float(crecimiento_ventas) < 10 else 'mantener'
            }
        }
        
        return sugerencias
    
    @staticmethod
    def obtener_notificaciones_pendientes(empresa):
        """Obtiene las notificaciones pendientes de una empresa"""
        return NotificacionMeta.objects.filter(
            empresa=empresa,
            leida=False
        ).order_by('-fecha_creacion')
    
    @staticmethod
    def marcar_notificacion_leida(notificacion_id):
        """Marca una notificación como leída"""
        try:
            notificacion = NotificacionMeta.objects.get(id=notificacion_id)
            notificacion.marcar_leida()
            return True
        except NotificacionMeta.DoesNotExist:
            return False 