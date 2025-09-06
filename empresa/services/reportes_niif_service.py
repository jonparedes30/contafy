"""Servicio para reportes NIIF mejorados"""
import logging
from decimal import Decimal
from django.db.models import Sum, Q, Count
from datetime import date, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

class ReportesNIIFService:
    """Servicio para generar reportes NIIF completos"""
    
    @staticmethod
    def generar_estado_situacion_financiera(empresa, fecha_corte=None):
        """Estado de Situación Financiera según NIIF"""
        from ..models import CuentaContable, MovimientoContable, CuentaPorCobrar, InstrumentoFinanciero
        
        if not fecha_corte:
            fecha_corte = date.today()
        
        # Obtener saldos de cuentas contables
        cuentas = CuentaContable.objects.filter(empresa=empresa)
        
        reporte = {
            'fecha_corte': fecha_corte,
            'activos_corrientes': {},
            'activos_no_corrientes': {},
            'pasivos_corrientes': {},
            'pasivos_no_corrientes': {},
            'patrimonio': {},
            'totales': {}
        }
        
        for cuenta in cuentas:
            saldo = cuenta.valor
            if abs(saldo) < 0.01:  # Ignorar saldos insignificantes
                continue
                
            if cuenta.tipo == 'activo':
                # Clasificar en corriente/no corriente
                if cuenta.nombre in ['Caja', 'Bancos', 'Cuentas por Cobrar', 'Inventario']:
                    reporte['activos_corrientes'][cuenta.nombre] = float(saldo)
                else:
                    reporte['activos_no_corrientes'][cuenta.nombre] = float(saldo)
                    
            elif cuenta.tipo == 'pasivo':
                if cuenta.nombre in ['Cuentas por Pagar', 'IVA por Pagar']:
                    reporte['pasivos_corrientes'][cuenta.nombre] = float(saldo)
                else:
                    reporte['pasivos_no_corrientes'][cuenta.nombre] = float(saldo)
                    
            elif cuenta.tipo == 'capital':
                reporte['patrimonio'][cuenta.nombre] = float(saldo)
        
        # Ajustar por deterioro de cuentas por cobrar
        deterioro_total = CuentaPorCobrar.objects.filter(
            empresa=empresa
        ).aggregate(total=Sum('deterioro_esperado'))['total'] or 0
        
        if deterioro_total > 0:
            reporte['activos_corrientes']['Provisión Deterioro CxC'] = -float(deterioro_total)
        
        # Calcular totales
        reporte['totales'] = {
            'activos_corrientes': sum(reporte['activos_corrientes'].values()),
            'activos_no_corrientes': sum(reporte['activos_no_corrientes'].values()),
            'total_activos': sum(reporte['activos_corrientes'].values()) + sum(reporte['activos_no_corrientes'].values()),
            'pasivos_corrientes': sum(reporte['pasivos_corrientes'].values()),
            'pasivos_no_corrientes': sum(reporte['pasivos_no_corrientes'].values()),
            'total_pasivos': sum(reporte['pasivos_corrientes'].values()) + sum(reporte['pasivos_no_corrientes'].values()),
            'total_patrimonio': sum(reporte['patrimonio'].values())
        }
        
        return reporte
    
    @staticmethod
    def generar_estado_resultados_niif(empresa, fecha_inicio, fecha_fin):
        """Estado de Resultados según NIIF 15"""
        from ..models import CuentaContable, MovimientoContable, ContratoVenta, ObligacionDesempeno
        
        reporte = {
            'periodo': f"{fecha_inicio} - {fecha_fin}",
            'ingresos_ordinarios': {},
            'costos_ventas': {},
            'gastos_operativos': {},
            'otros_ingresos': {},
            'gastos_financieros': {},
            'totales': {}
        }
        
        # Ingresos según NIIF 15
        ingresos_contratos = ObligacionDesempeno.objects.filter(
            contrato__empresa=empresa,
            satisfecha=True,
            fecha_satisfaccion__range=[fecha_inicio, fecha_fin]
        ).aggregate(total=Sum('precio_asignado'))['total'] or 0
        
        # Ingresos tradicionales
        try:
            cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre='Ventas')
            ingresos_ventas = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_ventas,
                tipo='credito',
                fecha__date__range=[fecha_inicio, fecha_fin]
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            ingresos_ventas = 0
        
        reporte['ingresos_ordinarios'] = {
            'Ventas Tradicionales': float(ingresos_ventas),
            'Ingresos por Contratos NIIF 15': float(ingresos_contratos)
        }
        
        # Costos de ventas
        try:
            cuenta_costos = CuentaContable.objects.get(empresa=empresa, nombre='Costo de Ventas')
            costos = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_costos,
                tipo='debito',
                fecha__date__range=[fecha_inicio, fecha_fin]
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            reporte['costos_ventas']['Costo de Ventas'] = float(costos)
        except CuentaContable.DoesNotExist:
            pass
        
        # Gastos operativos
        try:
            cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre='Gastos')
            gastos = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_gastos,
                tipo='debito',
                fecha__date__range=[fecha_inicio, fecha_fin]
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            reporte['gastos_operativos']['Gastos Operacionales'] = float(gastos)
        except CuentaContable.DoesNotExist:
            pass
        
        # Gastos por deterioro
        try:
            cuenta_deterioro = CuentaContable.objects.get(empresa=empresa, nombre='Deterioro Cuentas por Cobrar')
            deterioro = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_deterioro,
                tipo='debito',
                fecha__date__range=[fecha_inicio, fecha_fin]
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            if deterioro > 0:
                reporte['gastos_operativos']['Deterioro NIIF 9'] = float(deterioro)
        except CuentaContable.DoesNotExist:
            pass
        
        # Calcular totales
        total_ingresos = sum(reporte['ingresos_ordinarios'].values())
        total_costos = sum(reporte['costos_ventas'].values())
        total_gastos = sum(reporte['gastos_operativos'].values())
        
        reporte['totales'] = {
            'ingresos_ordinarios': total_ingresos,
            'utilidad_bruta': total_ingresos - total_costos,
            'gastos_operativos': total_gastos,
            'utilidad_operativa': total_ingresos - total_costos - total_gastos,
            'utilidad_neta': total_ingresos - total_costos - total_gastos
        }
        
        return reporte
    
    @staticmethod
    def generar_notas_explicativas_niif(empresa):
        """Genera notas explicativas según NIIF"""
        from ..models import CuentaPorCobrar, InstrumentoFinanciero, ContratoVenta, RevaluacionActivo
        
        notas = {
            'politicas_contables': {
                'reconocimiento_ingresos': 'Los ingresos se reconocen según NIIF 15 cuando se transfiere el control de bienes o servicios al cliente.',
                'instrumentos_financieros': 'Los instrumentos financieros se clasifican según NIIF 9 en costo amortizado o valor razonable.',
                'inventarios': 'Los inventarios se valúan al menor entre costo (método PEPS) y valor neto realizable según NIC 2.',
                'deterioro': 'Se aplica el modelo de pérdidas crediticias esperadas según NIIF 9.'
            },
            'cuentas_por_cobrar': {},
            'instrumentos_financieros': {},
            'contratos_niif15': {},
            'revaluaciones': {}
        }
        
        # Análisis de cuentas por cobrar
        cuentas_vencidas = CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado='pendiente',
            fecha_vencimiento__lt=date.today()
        )
        
        notas['cuentas_por_cobrar'] = {
            'total_cuentas': CuentaPorCobrar.objects.filter(empresa=empresa).count(),
            'cuentas_vencidas': cuentas_vencidas.count(),
            'deterioro_total': float(CuentaPorCobrar.objects.filter(empresa=empresa).aggregate(
                total=Sum('deterioro_esperado'))['total'] or 0),
            'politica_deterioro': 'Se aplican tasas de deterioro del 1% general, 2% > 30 días, 5% > 60 días, 10% > 90 días.'
        }
        
        # Instrumentos financieros
        instrumentos = InstrumentoFinanciero.objects.filter(empresa=empresa)
        notas['instrumentos_financieros'] = {
            'total_instrumentos': instrumentos.count(),
            'por_categoria': {
                categoria[0]: instrumentos.filter(categoria=categoria[0]).count()
                for categoria in InstrumentoFinanciero.CATEGORIA_CHOICES
            }
        }
        
        # Contratos NIIF 15
        contratos = ContratoVenta.objects.filter(empresa=empresa)
        notas['contratos_niif15'] = {
            'total_contratos': contratos.count(),
            'contratos_activos': contratos.filter(estado='activo').count(),
            'ingresos_diferidos': float(contratos.filter(estado='activo').aggregate(
                total=Sum('obligaciones__precio_asignado'))['total'] or 0)
        }
        
        # Revaluaciones
        revaluaciones = RevaluacionActivo.objects.filter(empresa=empresa)
        notas['revaluaciones'] = {
            'total_revaluaciones': revaluaciones.count(),
            'superavit_total': float(sum(r.superavit_revaluacion for r in revaluaciones))
        }
        
        return notas
    
    @staticmethod
    def generar_reporte_cumplimiento_completo(empresa):
        """Reporte completo de cumplimiento NIIF"""
        from ..services.niif_service import NIIFService
        
        cumplimiento_basico = NIIFService.generar_reporte_cumplimiento_niif(empresa)
        
        # Análisis adicional
        reporte_completo = {
            'cumplimiento_basico': cumplimiento_basico,
            'estado_situacion_financiera': ReportesNIIFService.generar_estado_situacion_financiera(empresa),
            'notas_explicativas': ReportesNIIFService.generar_notas_explicativas_niif(empresa),
            'recomendaciones': ReportesNIIFService._generar_recomendaciones_mejora(empresa, cumplimiento_basico)
        }
        
        return reporte_completo
    
    @staticmethod
    def _generar_recomendaciones_mejora(empresa, cumplimiento):
        """Genera recomendaciones específicas de mejora"""
        recomendaciones = []
        
        if cumplimiento['niif_9']['porcentaje'] < 90:
            recomendaciones.append({
                'area': 'NIIF 9 - Instrumentos Financieros',
                'prioridad': 'Alta',
                'descripcion': 'Actualizar deterioro de cuentas por cobrar regularmente',
                'accion': 'Ejecutar comando: python manage.py actualizar_deterioro'
            })
        
        if not cumplimiento['niif_15']['implementado']:
            recomendaciones.append({
                'area': 'NIIF 15 - Reconocimiento de Ingresos',
                'prioridad': 'Media',
                'descripcion': 'Implementar contratos para ventas complejas',
                'accion': 'Crear contratos para ventas > $10,000'
            })
        
        if not cumplimiento['instrumentos_financieros']['implementado']:
            recomendaciones.append({
                'area': 'Instrumentos Financieros',
                'prioridad': 'Baja',
                'descripcion': 'Registrar instrumentos financieros de la empresa',
                'accion': 'Crear registros de inversiones, préstamos, etc.'
            })
        
        return recomendaciones