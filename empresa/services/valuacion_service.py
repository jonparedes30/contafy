"""
Servicio de Valuación de Empresas
Calcula el valor estimado de la empresa usando múltiples métodos
"""
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import timedelta
from empresa.models import Empresa, MovimientoContable, CuentaContable
from decimal import Decimal
import math

class ServicioValuacion:
    
    @staticmethod
    def calcular_valuacion_completa(empresa):
        """Calcula valuación usando múltiples métodos"""
        
        # Obtener datos financieros
        datos_financieros = ServicioValuacion._obtener_datos_financieros(empresa)
        
        # Métodos de valuación
        valuacion_dcf = ServicioValuacion._valuacion_dcf(datos_financieros)
        valuacion_multiplos = ServicioValuacion._valuacion_multiplos(empresa, datos_financieros)
        valuacion_libros = ServicioValuacion._valuacion_libros(empresa, datos_financieros)
        
        # Promedio ponderado
        valuacion_promedio = ServicioValuacion._calcular_promedio_ponderado([
            (valuacion_dcf, 0.4),
            (valuacion_multiplos, 0.4), 
            (valuacion_libros, 0.2)
        ])
        
        return {
            'valuacion_dcf': valuacion_dcf,
            'valuacion_multiplos': valuacion_multiplos,
            'valuacion_libros': valuacion_libros,
            'valuacion_promedio': valuacion_promedio,
            'datos_financieros': datos_financieros,
            'recomendaciones': ServicioValuacion._generar_recomendaciones_valuacion(
                valuacion_promedio, datos_financieros
            )
        }
    
    @staticmethod
    def _obtener_datos_financieros(empresa):
        """Obtiene datos financieros históricos"""
        hoy = timezone.now()
        
        # Últimos 12 meses
        hace_12_meses = hoy - timedelta(days=365)
        
        try:
            # Ventas anuales
            cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
            ventas_anuales = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                fecha__gte=hace_12_meses
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            # Gastos anuales
            cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
            gastos_anuales = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_gastos, tipo='debito',
                fecha__gte=hace_12_meses
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            # Activos (aproximado)
            cuentas_activos = CuentaContable.objects.filter(empresa=empresa, tipo='activo')
            activos_totales = sum(cuenta.valor for cuenta in cuentas_activos)
            
            # Pasivos (aproximado)
            cuentas_pasivos = CuentaContable.objects.filter(empresa=empresa, tipo='pasivo')
            pasivos_totales = sum(cuenta.valor for cuenta in cuentas_pasivos)
            
        except CuentaContable.DoesNotExist:
            ventas_anuales = gastos_anuales = activos_totales = pasivos_totales = 0
        
        utilidad_neta = ventas_anuales - gastos_anuales
        patrimonio = activos_totales - pasivos_totales
        
        # Calcular tendencia (últimos 6 meses vs anteriores 6)
        hace_6_meses = hoy - timedelta(days=180)
        
        try:
            ventas_recientes = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                fecha__gte=hace_6_meses
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            ventas_anteriores = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                fecha__gte=hace_12_meses, fecha__lt=hace_6_meses
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            tasa_crecimiento = ((ventas_recientes - ventas_anteriores) / ventas_anteriores * 100) if ventas_anteriores > 0 else 0
        except:
            tasa_crecimiento = 0
        
        return {
            'ventas_anuales': float(ventas_anuales),
            'gastos_anuales': float(gastos_anuales),
            'utilidad_neta': float(utilidad_neta),
            'activos_totales': float(activos_totales),
            'pasivos_totales': float(pasivos_totales),
            'patrimonio': float(patrimonio),
            'tasa_crecimiento': float(tasa_crecimiento),
            'margen_neto': (utilidad_neta / ventas_anuales * 100) if ventas_anuales > 0 else 0
        }
    
    @staticmethod
    def _valuacion_dcf(datos):
        """Valuación por Flujo de Caja Descontado"""
        utilidad_neta = datos['utilidad_neta']
        tasa_crecimiento = max(datos['tasa_crecimiento'], 0) / 100
        
        # Tasa de descuento (WACC estimado para PyMEs)
        tasa_descuento = 0.15  # 15% típico para PyMEs
        
        # Proyección a 5 años
        flujos_proyectados = []
        flujo_base = utilidad_neta
        
        for año in range(1, 6):
            flujo_proyectado = flujo_base * ((1 + tasa_crecimiento) ** año)
            valor_presente = flujo_proyectado / ((1 + tasa_descuento) ** año)
            flujos_proyectados.append(valor_presente)
        
        # Valor terminal (crecimiento perpetuo del 2%)
        crecimiento_terminal = 0.02
        flujo_terminal = flujos_proyectados[-1] * (1 + crecimiento_terminal)
        valor_terminal = flujo_terminal / (tasa_descuento - crecimiento_terminal)
        valor_terminal_presente = valor_terminal / ((1 + tasa_descuento) ** 5)
        
        valor_empresa = sum(flujos_proyectados) + valor_terminal_presente
        
        return max(valor_empresa, 0)  # No puede ser negativo
    
    @staticmethod
    def _valuacion_multiplos(empresa, datos):
        """Valuación por múltiplos del sector"""
        ventas_anuales = datos['ventas_anuales']
        utilidad_neta = datos['utilidad_neta']
        
        # Múltiplos típicos por sector (simplificado)
        multiplos_sector = {
            'comercial': {'precio_ventas': 0.8, 'precio_utilidad': 12},
            'manufactura': {'precio_ventas': 1.2, 'precio_utilidad': 15},
            'servicios': {'precio_ventas': 1.5, 'precio_utilidad': 18}
        }
        
        multiplos = multiplos_sector.get(empresa.categoria, multiplos_sector['comercial'])
        
        # Valuación por ventas
        valor_por_ventas = ventas_anuales * multiplos['precio_ventas']
        
        # Valuación por utilidades (P/E)
        valor_por_utilidad = utilidad_neta * multiplos['precio_utilidad'] if utilidad_neta > 0 else 0
        
        # Promedio de ambos métodos
        return (valor_por_ventas + valor_por_utilidad) / 2
    
    @staticmethod
    def _valuacion_libros(empresa, datos):
        """Valuación por valor en libros ajustado"""
        patrimonio = datos['patrimonio']
        
        # Ajustes típicos para PyMEs
        factor_ajuste = 1.2 if datos['utilidad_neta'] > 0 else 0.8
        
        return max(patrimonio * factor_ajuste, 0)
    
    @staticmethod
    def _calcular_promedio_ponderado(valuaciones_pesos):
        """Calcula promedio ponderado de valuaciones"""
        total_valor = 0
        total_peso = 0
        
        for valor, peso in valuaciones_pesos:
            if valor > 0:  # Solo considerar valuaciones positivas
                total_valor += valor * peso
                total_peso += peso
        
        return total_valor / total_peso if total_peso > 0 else 0
    
    @staticmethod
    def _generar_recomendaciones_valuacion(valuacion, datos):
        """Genera recomendaciones basadas en la valuación"""
        recomendaciones = []
        
        # Análisis de rentabilidad
        if datos['margen_neto'] < 5:
            recomendaciones.append({
                'tipo': 'warning',
                'area': 'Rentabilidad',
                'mensaje': f'Margen neto bajo ({datos["margen_neto"]:.1f}%) afecta la valuación',
                'impacto': 'Alto'
            })
        
        # Análisis de crecimiento
        if datos['tasa_crecimiento'] < 0:
            recomendaciones.append({
                'tipo': 'danger',
                'area': 'Crecimiento',
                'mensaje': 'Tendencia negativa reduce significativamente el valor',
                'impacto': 'Crítico'
            })
        elif datos['tasa_crecimiento'] > 20:
            recomendaciones.append({
                'tipo': 'success',
                'area': 'Crecimiento',
                'mensaje': f'Excelente crecimiento ({datos["tasa_crecimiento"]:.1f}%) aumenta el valor',
                'impacto': 'Positivo'
            })
        
        # Análisis de estructura financiera
        if datos['pasivos_totales'] > datos['activos_totales'] * 0.7:
            recomendaciones.append({
                'tipo': 'warning',
                'area': 'Endeudamiento',
                'mensaje': 'Alto nivel de deuda reduce el valor de la empresa',
                'impacto': 'Medio'
            })
        
        return recomendaciones
    
    @staticmethod
    def proyectar_valor_futuro(empresa, años=3):
        """Proyecta el valor futuro de la empresa"""
        valuacion_actual = ServicioValuacion.calcular_valuacion_completa(empresa)
        datos = valuacion_actual['datos_financieros']
        
        tasa_crecimiento = max(datos['tasa_crecimiento'], 0) / 100
        valor_actual = valuacion_actual['valuacion_promedio']
        
        proyecciones = []
        for año in range(1, años + 1):
            valor_proyectado = valor_actual * ((1 + tasa_crecimiento) ** año)
            proyecciones.append({
                'año': año,
                'valor_proyectado': valor_proyectado,
                'crecimiento_acumulado': ((valor_proyectado / valor_actual - 1) * 100) if valor_actual > 0 else 0
            })
        
        return {
            'valor_actual': valor_actual,
            'proyecciones': proyecciones,
            'tasa_crecimiento_anual': tasa_crecimiento * 100
        }