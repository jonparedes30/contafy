"""
Benchmarking Avanzado con Valuación y Análisis Predictivo
Integra: comparación sectorial + valuación + proyecciones + análisis de riesgo
"""
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from empresa.models import Empresa, MovimientoContable, CuentaContable
from empresa.services.benchmarking_real_service import BenchmarkingRealService
from decimal import Decimal
import math

class BenchmarkingAvanzadoService:
    
    @staticmethod
    def obtener_benchmarking_completo_avanzado(empresa):
        """Benchmarking completo con valuación y análisis predictivo"""
        
        # Benchmarking base
        benchmarking_base = BenchmarkingRealService.obtener_benchmarking_completo(empresa)
        
        # Valuación comparativa
        valuacion_comparativa = BenchmarkingAvanzadoService._calcular_valuacion_comparativa(empresa)
        
        # Análisis predictivo
        analisis_predictivo = BenchmarkingAvanzadoService._calcular_analisis_predictivo(empresa)
        
        # Proyecciones de posición
        proyecciones_posicion = BenchmarkingAvanzadoService._proyectar_posicion_futura(empresa)
        
        # Combinar todo
        return {
            **benchmarking_base,
            'valuacion_comparativa': valuacion_comparativa,
            'analisis_predictivo': analisis_predictivo,
            'proyecciones_posicion': proyecciones_posicion,
            'tamaño_empresa': BenchmarkingAvanzadoService._clasificar_tamaño_empresa(empresa)
        }
    
    @staticmethod
    def _calcular_valuacion_comparativa(empresa):
        """Calcula valuación y la compara con el sector"""
        
        # Datos financieros propios
        datos_propios = BenchmarkingAvanzadoService._obtener_datos_financieros(empresa)
        
        # Valuación propia (método simplificado)
        valuacion_propia = BenchmarkingAvanzadoService._calcular_valuacion_simple(datos_propios)
        
        # Obtener empresas similares para comparar valuación
        empresas_similares = Empresa.objects.filter(
            categoria=empresa.categoria
        ).exclude(id=empresa.id)
        
        valuaciones_sector = []
        for emp in empresas_similares:
            datos_emp = BenchmarkingAvanzadoService._obtener_datos_financieros(emp)
            if datos_emp['ventas_anuales'] > 0:
                valuacion_emp = BenchmarkingAvanzadoService._calcular_valuacion_simple(datos_emp)
                valuaciones_sector.append(valuacion_emp)
        
        if len(valuaciones_sector) >= 3:
            valuacion_promedio_sector = sum(valuaciones_sector) / len(valuaciones_sector)
            valuacion_mediana_sector = sorted(valuaciones_sector)[len(valuaciones_sector)//2]
            
            # Percentil de la empresa
            empresas_menores = sum(1 for v in valuaciones_sector if v < valuacion_propia)
            percentil_valuacion = (empresas_menores / len(valuaciones_sector)) * 100
            
            return {
                'valuacion_propia': valuacion_propia,
                'valuacion_promedio_sector': valuacion_promedio_sector,
                'valuacion_mediana_sector': valuacion_mediana_sector,
                'percentil_valuacion': percentil_valuacion,
                'total_empresas_comparadas': len(valuaciones_sector),
                'tiene_datos': True
            }
        
        return {'tiene_datos': False, 'razon': 'Datos insuficientes para comparación de valuación'}
    
    @staticmethod
    def _calcular_valuacion_simple(datos):
        """Método simplificado de valuación para comparación"""
        ventas = datos['ventas_anuales']
        utilidad = datos['utilidad_neta']
        
        # Múltiplo conservador: 2x ventas + 10x utilidad (si es positiva)
        valuacion = ventas * 2
        if utilidad > 0:
            valuacion += utilidad * 10
        
        return max(valuacion, ventas * 0.5)  # Mínimo 0.5x ventas
    
    @staticmethod
    def _calcular_analisis_predictivo(empresa):
        """Análisis predictivo de riesgo y oportunidades"""
        datos = BenchmarkingAvanzadoService._obtener_datos_financieros(empresa)
        
        # Altman Z-Score simplificado para PyMEs
        z_score = BenchmarkingAvanzadoService._calcular_altman_z_score(datos)
        
        # Probabilidad de crecimiento
        prob_crecimiento = BenchmarkingAvanzadoService._calcular_probabilidad_crecimiento(datos)
        
        # Alertas tempranas
        alertas = BenchmarkingAvanzadoService._generar_alertas_tempranas(datos)
        
        return {
            'z_score': z_score,
            'riesgo_quiebra': BenchmarkingAvanzadoService._interpretar_z_score(z_score),
            'probabilidad_crecimiento': prob_crecimiento,
            'alertas_tempranas': alertas,
            'tendencia_general': BenchmarkingAvanzadoService._evaluar_tendencia_general(datos)
        }
    
    @staticmethod
    def _calcular_altman_z_score(datos):
        """Altman Z-Score adaptado para PyMEs"""
        if datos['activos_totales'] == 0:
            return 0
        
        # Ratios simplificados
        capital_trabajo = datos['activos_totales'] - datos['pasivos_totales']
        ratio_liquidez = capital_trabajo / datos['activos_totales']
        ratio_rentabilidad = datos['utilidad_neta'] / datos['activos_totales'] if datos['activos_totales'] > 0 else 0
        ratio_ventas = datos['ventas_anuales'] / datos['activos_totales'] if datos['activos_totales'] > 0 else 0
        
        # Z-Score simplificado
        z_score = (1.2 * ratio_liquidez) + (1.4 * ratio_rentabilidad) + (1.0 * ratio_ventas)
        
        return z_score
    
    @staticmethod
    def _interpretar_z_score(z_score):
        """Interpreta el Z-Score"""
        if z_score > 2.6:
            return {'nivel': 'Bajo', 'descripcion': 'Empresa financieramente sólida'}
        elif z_score > 1.8:
            return {'nivel': 'Medio', 'descripcion': 'Situación financiera estable'}
        else:
            return {'nivel': 'Alto', 'descripcion': 'Requiere atención financiera'}
    
    @staticmethod
    def _calcular_probabilidad_crecimiento(datos):
        """Calcula probabilidad de crecimiento basada en indicadores"""
        factores = []
        
        # Factor rentabilidad
        if datos['margen_neto'] > 10:
            factores.append(30)
        elif datos['margen_neto'] > 5:
            factores.append(20)
        else:
            factores.append(10)
        
        # Factor crecimiento histórico
        if datos['tasa_crecimiento'] > 15:
            factores.append(25)
        elif datos['tasa_crecimiento'] > 5:
            factores.append(15)
        else:
            factores.append(5)
        
        # Factor liquidez
        if datos['activos_totales'] > datos['pasivos_totales'] * 1.5:
            factores.append(20)
        else:
            factores.append(10)
        
        # Factor ventas
        if datos['ventas_anuales'] > 50000:
            factores.append(25)
        elif datos['ventas_anuales'] > 20000:
            factores.append(15)
        else:
            factores.append(10)
        
        return min(sum(factores), 100)
    
    @staticmethod
    def _generar_alertas_tempranas(datos):
        """Genera alertas tempranas de problemas"""
        alertas = []
        
        if datos['margen_neto'] < 0:
            alertas.append({
                'tipo': 'critico',
                'mensaje': 'Margen negativo - Revisar costos urgentemente',
                'prioridad': 'Alta'
            })
        
        if datos['tasa_crecimiento'] < -10:
            alertas.append({
                'tipo': 'warning',
                'mensaje': 'Decrecimiento significativo en ventas',
                'prioridad': 'Alta'
            })
        
        if datos['pasivos_totales'] > datos['activos_totales'] * 0.8:
            alertas.append({
                'tipo': 'warning',
                'mensaje': 'Alto nivel de endeudamiento',
                'prioridad': 'Media'
            })
        
        if datos['ventas_anuales'] < 10000:
            alertas.append({
                'tipo': 'info',
                'mensaje': 'Oportunidad de crecimiento en ventas',
                'prioridad': 'Media'
            })
        
        return alertas
    
    @staticmethod
    def _evaluar_tendencia_general(datos):
        """Evalúa la tendencia general de la empresa"""
        puntuacion = 0
        
        # Rentabilidad
        if datos['margen_neto'] > 15:
            puntuacion += 3
        elif datos['margen_neto'] > 5:
            puntuacion += 2
        elif datos['margen_neto'] > 0:
            puntuacion += 1
        
        # Crecimiento
        if datos['tasa_crecimiento'] > 20:
            puntuacion += 3
        elif datos['tasa_crecimiento'] > 10:
            puntuacion += 2
        elif datos['tasa_crecimiento'] > 0:
            puntuacion += 1
        
        # Solvencia
        if datos['activos_totales'] > datos['pasivos_totales'] * 2:
            puntuacion += 2
        elif datos['activos_totales'] > datos['pasivos_totales']:
            puntuacion += 1
        
        if puntuacion >= 7:
            return {'nivel': 'Excelente', 'color': 'success'}
        elif puntuacion >= 5:
            return {'nivel': 'Buena', 'color': 'primary'}
        elif puntuacion >= 3:
            return {'nivel': 'Regular', 'color': 'warning'}
        else:
            return {'nivel': 'Preocupante', 'color': 'danger'}
    
    @staticmethod
    def _proyectar_posicion_futura(empresa):
        """Proyecta la posición futura en el sector"""
        datos = BenchmarkingAvanzadoService._obtener_datos_financieros(empresa)
        
        # Proyección simple basada en tendencias
        crecimiento_anual = max(datos['tasa_crecimiento'], 0) / 100
        
        proyecciones = []
        for año in range(1, 4):  # 3 años
            factor_crecimiento = (1 + crecimiento_anual) ** año
            
            ventas_proyectadas = datos['ventas_anuales'] * factor_crecimiento
            utilidad_proyectada = datos['utilidad_neta'] * factor_crecimiento
            
            # Posición estimada (simplificada)
            if ventas_proyectadas > 100000:
                posicion_estimada = 'Top 10%'
            elif ventas_proyectadas > 50000:
                posicion_estimada = 'Top 25%'
            elif ventas_proyectadas > 20000:
                posicion_estimada = 'Top 50%'
            else:
                posicion_estimada = 'Bottom 50%'
            
            proyecciones.append({
                'año': año,
                'ventas_proyectadas': ventas_proyectadas,
                'utilidad_proyectada': utilidad_proyectada,
                'posicion_estimada': posicion_estimada
            })
        
        return proyecciones
    
    @staticmethod
    def _clasificar_tamaño_empresa(empresa):
        """Clasifica el tamaño de la empresa"""
        datos = BenchmarkingAvanzadoService._obtener_datos_financieros(empresa)
        ventas = datos['ventas_anuales']
        
        if ventas > 500000:
            return {'categoria': 'Grande', 'descripcion': 'Empresa grande del sector'}
        elif ventas > 100000:
            return {'categoria': 'Mediana', 'descripcion': 'Empresa mediana del sector'}
        elif ventas > 20000:
            return {'categoria': 'Pequeña', 'descripcion': 'Pequeña empresa del sector'}
        else:
            return {'categoria': 'Micro', 'descripcion': 'Microempresa del sector'}
    
    @staticmethod
    def _obtener_datos_financieros(empresa):
        """Obtiene datos financieros (reutiliza lógica del servicio de valuación)"""
        hoy = timezone.now()
        hace_12_meses = hoy - timedelta(days=365)
        hace_6_meses = hoy - timedelta(days=180)
        
        try:
            cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
            ventas_anuales = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                fecha__gte=hace_12_meses
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            ventas_recientes = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                fecha__gte=hace_6_meses
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            ventas_anteriores = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                fecha__gte=hace_12_meses, fecha__lt=hace_6_meses
            ).aggregate(total=Sum('monto'))['total'] or 0
            
        except CuentaContable.DoesNotExist:
            ventas_anuales = ventas_recientes = ventas_anteriores = 0
        
        try:
            cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
            gastos_anuales = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_gastos, tipo='debito',
                fecha__gte=hace_12_meses
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            gastos_anuales = 0
        
        # Activos y pasivos
        cuentas_activos = CuentaContable.objects.filter(empresa=empresa, tipo='activo')
        activos_totales = sum(cuenta.valor for cuenta in cuentas_activos)
        
        cuentas_pasivos = CuentaContable.objects.filter(empresa=empresa, tipo='pasivo')
        pasivos_totales = sum(cuenta.valor for cuenta in cuentas_pasivos)
        
        utilidad_neta = ventas_anuales - gastos_anuales
        tasa_crecimiento = ((ventas_recientes - ventas_anteriores) / ventas_anteriores * 100) if ventas_anteriores > 0 else 0
        margen_neto = (utilidad_neta / ventas_anuales * 100) if ventas_anuales > 0 else 0
        
        return {
            'ventas_anuales': float(ventas_anuales),
            'gastos_anuales': float(gastos_anuales),
            'utilidad_neta': float(utilidad_neta),
            'activos_totales': float(activos_totales),
            'pasivos_totales': float(pasivos_totales),
            'tasa_crecimiento': float(tasa_crecimiento),
            'margen_neto': float(margen_neto)
        }