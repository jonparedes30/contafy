"""Servicio para operaciones NIIF avanzadas"""
import logging
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from datetime import date, timedelta

logger = logging.getLogger(__name__)

class NIIFService:
    """Servicio para manejar operaciones NIIF avanzadas"""
    
    @staticmethod
    def evaluar_deterioro_instrumentos(empresa):
        """Evalúa deterioro de instrumentos financieros según NIIF 9"""
        from ..models import InstrumentoFinanciero, CuentaContable, MovimientoContable
        
        instrumentos = InstrumentoFinanciero.objects.filter(
            empresa=empresa,
            tipo='activo_financiero'
        )
        
        total_deterioro = 0
        for instrumento in instrumentos:
            deterioro = instrumento.calcular_deterioro_niif9()
            if deterioro > 0:
                # Crear asientos de deterioro
                cuenta_deterioro = CuentaContable.objects.get_or_create(
                    empresa=empresa,
                    nombre='Deterioro Instrumentos Financieros',
                    defaults={'tipo': 'gasto'}
                )[0]
                
                cuenta_provision = CuentaContable.objects.get_or_create(
                    empresa=empresa,
                    nombre='Provisión Deterioro IF',
                    defaults={'tipo': 'activo'}
                )[0]
                
                MovimientoContable.objects.create(
                    empresa=empresa,
                    cuenta_fk=cuenta_deterioro,
                    tipo='debito',
                    monto=deterioro,
                    descripcion=f'Deterioro {instrumento.nombre}'
                )
                
                MovimientoContable.objects.create(
                    empresa=empresa,
                    cuenta_fk=cuenta_provision,
                    tipo='credito',
                    monto=deterioro,
                    descripcion=f'Provisión deterioro {instrumento.nombre}'
                )
                
                total_deterioro += deterioro
        
        return total_deterioro
    
    @staticmethod
    def procesar_contratos_niif15(empresa):
        """Procesa contratos según NIIF 15"""
        from ..models import ContratoVenta, ObligacionDesempeno
        
        contratos_activos = ContratoVenta.objects.filter(
            empresa=empresa,
            estado='activo'
        )
        
        ingresos_reconocidos = 0
        for contrato in contratos_activos:
            for obligacion in contrato.obligaciones.filter(satisfecha=False):
                if obligacion.porcentaje_completado >= 100:
                    obligacion.reconocer_ingreso()
                    ingresos_reconocidos += obligacion.precio_asignado
        
        return ingresos_reconocidos
    
    @staticmethod
    def calcular_valor_razonable_activos(empresa):
        """Calcula valor razonable de activos para revaluación"""
        from ..models import RevaluacionActivo
        
        # Simulación de revaluación automática
        revaluaciones = RevaluacionActivo.objects.filter(
            empresa=empresa,
            fecha_revaluacion__gte=date.today() - timedelta(days=365)
        )
        
        total_superavit = sum(r.superavit_revaluacion for r in revaluaciones)
        return total_superavit
    
    @staticmethod
    def generar_reporte_cumplimiento_niif(empresa):
        """Genera reporte completo de cumplimiento NIIF"""
        from ..models import CuentaPorCobrar, MovimientoInventario, InstrumentoFinanciero
        
        # Análisis NIIF 9 - Instrumentos Financieros
        cuentas_deterioro = CuentaPorCobrar.objects.filter(
            empresa=empresa,
            deterioro_esperado__gt=0
        ).count()
        
        total_cuentas = CuentaPorCobrar.objects.filter(empresa=empresa).count()
        
        # Análisis NIC 2 - Inventarios
        movimientos_peps = MovimientoInventario.objects.filter(empresa=empresa).count()
        
        # Análisis NIIF 15 - Ingresos
        from ..models import ContratoVenta
        contratos_niif15 = ContratoVenta.objects.filter(empresa=empresa).count()
        
        # Instrumentos financieros
        instrumentos = InstrumentoFinanciero.objects.filter(empresa=empresa).count()
        
        cumplimiento = {
            'niif_9': {
                'cuentas_con_deterioro': cuentas_deterioro,
                'total_cuentas': total_cuentas,
                'porcentaje': (cuentas_deterioro / total_cuentas * 100) if total_cuentas > 0 else 100
            },
            'nic_2': {
                'movimientos_peps': movimientos_peps,
                'implementado': movimientos_peps > 0
            },
            'niif_15': {
                'contratos_registrados': contratos_niif15,
                'implementado': contratos_niif15 > 0
            },
            'instrumentos_financieros': {
                'total_instrumentos': instrumentos,
                'implementado': instrumentos > 0
            }
        }
        
        # Calcular puntuación general
        puntos = 0
        if cumplimiento['niif_9']['porcentaje'] > 80: puntos += 25
        if cumplimiento['nic_2']['implementado']: puntos += 25
        if cumplimiento['niif_15']['implementado']: puntos += 25
        if cumplimiento['instrumentos_financieros']['implementado']: puntos += 25
        
        cumplimiento['puntuacion_general'] = puntos
        cumplimiento['nivel_cumplimiento'] = 'Excelente' if puntos >= 90 else 'Bueno' if puntos >= 70 else 'Regular' if puntos >= 50 else 'Deficiente'
        
        return cumplimiento
    
    @staticmethod
    @transaction.atomic
    def ejecutar_cierre_niif(empresa, fecha_cierre=None):
        """Ejecuta proceso de cierre según NIIF"""
        if not fecha_cierre:
            fecha_cierre = date.today()
        
        resultados = {
            'deterioro_actualizado': 0,
            'ingresos_reconocidos': 0,
            'revaluaciones_procesadas': 0,
            'instrumentos_evaluados': 0
        }
        
        try:
            # 1. Actualizar deterioro NIIF 9
            from ..models import CuentaPorCobrar
            cuentas = CuentaPorCobrar.objects.filter(empresa=empresa, estado='pendiente')
            for cuenta in cuentas:
                cuenta.actualizar_deterioro()
                resultados['deterioro_actualizado'] += 1
            
            # 2. Procesar contratos NIIF 15
            ingresos = NIIFService.procesar_contratos_niif15(empresa)
            resultados['ingresos_reconocidos'] = float(ingresos)
            
            # 3. Evaluar instrumentos financieros
            deterioro_if = NIIFService.evaluar_deterioro_instrumentos(empresa)
            resultados['instrumentos_evaluados'] = float(deterioro_if)
            
            # 4. Procesar revaluaciones
            superavit = NIIFService.calcular_valor_razonable_activos(empresa)
            resultados['revaluaciones_procesadas'] = float(superavit)
            
            logger.info(f"Cierre NIIF completado para {empresa.nombre}: {resultados}")
            
        except Exception as e:
            logger.error(f"Error en cierre NIIF para {empresa.nombre}: {str(e)}")
            raise
        
        return resultados