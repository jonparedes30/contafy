"""
Servicio de Predicciones Avanzadas para CONTAFY
"""
import numpy as np
from datetime import datetime, date, timedelta
from django.db.models import Sum, Avg, Count, Q
from empresa.models import Venta, Gasto, Compra, Producto, CuentaContable, MovimientoContable
from decimal import Decimal
import math

class PrediccionesAvanzadas:
    """Servicio de predicciones financieras avanzadas"""
    
    def __init__(self, empresa):
        self.empresa = empresa
    
    def predecir_flujo_caja(self, meses=6):
        """Predicción de flujo de caja para los próximos meses"""
        try:
            # Obtener datos históricos
            datos_historicos = self._obtener_datos_flujo_historico(12)  # 12 meses de historia
            
            if len(datos_historicos) < 3:
                return self._prediccion_flujo_simple(meses)
            
            # Análisis de tendencias
            tendencia_ingresos = self._calcular_tendencia([d['ingresos'] for d in datos_historicos])
            tendencia_egresos = self._calcular_tendencia([d['egresos'] for d in datos_historicos])
            
            # Análisis de estacionalidad
            estacionalidad_ingresos = self._calcular_estacionalidad([d['ingresos'] for d in datos_historicos])
            estacionalidad_egresos = self._calcular_estacionalidad([d['egresos'] for d in datos_historicos])
            
            # Generar predicciones
            predicciones = []
            fecha_actual = date.today()
            
            for i in range(meses):
                # Calcular fecha del mes a predecir
                if fecha_actual.month + i > 12:
                    mes_prediccion = (fecha_actual.month + i) % 12
                    if mes_prediccion == 0:
                        mes_prediccion = 12
                else:
                    mes_prediccion = fecha_actual.month + i
                
                # Predicción base con tendencia
                ingresos_base = datos_historicos[-1]['ingresos'] + (tendencia_ingresos * (i + 1))
                egresos_base = datos_historicos[-1]['egresos'] + (tendencia_egresos * (i + 1))
                
                # Aplicar factor estacional
                factor_estacional_ing = estacionalidad_ingresos.get(mes_prediccion, 1.0)
                factor_estacional_egr = estacionalidad_egresos.get(mes_prediccion, 1.0)
                
                ingresos_predichos = max(0, ingresos_base * factor_estacional_ing)
                egresos_predichos = max(0, egresos_base * factor_estacional_egr)
                
                flujo_neto = ingresos_predichos - egresos_predichos
                
                # Calcular saldo acumulado
                saldo_anterior = predicciones[-1]['saldo_final'] if predicciones else self._obtener_saldo_actual()
                saldo_final = saldo_anterior + flujo_neto
                
                predicciones.append({
                    'mes': mes_prediccion,
                    'ingresos_predichos': round(ingresos_predichos, 2),
                    'egresos_predichos': round(egresos_predichos, 2),
                    'flujo_neto': round(flujo_neto, 2),
                    'saldo_inicial': round(saldo_anterior, 2),
                    'saldo_final': round(saldo_final, 2),
                    'riesgo_liquidez': 'Alto' if saldo_final < 0 else 'Medio' if saldo_final < 1000 else 'Bajo'
                })
            
            # Análisis de riesgos
            analisis_riesgos = self._analizar_riesgos_flujo_caja(predicciones)
            
            return {
                'success': True,
                'predicciones': predicciones,
                'tendencia_ingresos': round(tendencia_ingresos, 2),
                'tendencia_egresos': round(tendencia_egresos, 2),
                'analisis_riesgos': analisis_riesgos,
                'recomendaciones': self._generar_recomendaciones_flujo(predicciones),
                'confianza': self._calcular_confianza_prediccion(len(datos_historicos))
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Error en predicción de flujo de caja: {str(e)}'}
    
    def detectar_riesgo_quiebra(self):
        """Detecta riesgo de quiebra usando indicadores financieros"""
        try:
            # Obtener datos financieros actuales
            datos_actuales = self._obtener_datos_financieros_actuales()
            
            # Calcular indicadores de riesgo
            indicadores = {}
            
            # 1. Ratio de liquidez
            if datos_actuales['pasivos_corrientes'] > 0:
                liquidez = datos_actuales['activos_corrientes'] / datos_actuales['pasivos_corrientes']
                indicadores['liquidez'] = {
                    'valor': round(liquidez, 2),
                    'riesgo': 'Alto' if liquidez < 1.0 else 'Medio' if liquidez < 1.5 else 'Bajo',
                    'descripcion': 'Capacidad de pagar deudas a corto plazo'
                }
            
            # 2. Ratio de endeudamiento
            if datos_actuales['activos_totales'] > 0:
                endeudamiento = datos_actuales['pasivos_totales'] / datos_actuales['activos_totales']
                indicadores['endeudamiento'] = {
                    'valor': round(endeudamiento * 100, 1),
                    'riesgo': 'Alto' if endeudamiento > 0.7 else 'Medio' if endeudamiento > 0.5 else 'Bajo',
                    'descripcion': 'Porcentaje de activos financiados con deuda'
                }
            
            # 3. Flujo de caja operativo
            flujo_operativo = datos_actuales['ingresos_mes'] - datos_actuales['gastos_operativos']
            indicadores['flujo_operativo'] = {
                'valor': round(flujo_operativo, 2),
                'riesgo': 'Alto' if flujo_operativo < 0 else 'Medio' if flujo_operativo < 500 else 'Bajo',
                'descripcion': 'Efectivo generado por operaciones'
            }
            
            # 4. Tendencia de ventas
            tendencia_ventas = self._calcular_tendencia_ventas_trimestral()
            indicadores['tendencia_ventas'] = {
                'valor': round(tendencia_ventas, 1),
                'riesgo': 'Alto' if tendencia_ventas < -20 else 'Medio' if tendencia_ventas < 0 else 'Bajo',
                'descripcion': 'Cambio porcentual en ventas (últimos 3 meses)'
            }
            
            # 5. Cobertura de gastos fijos
            gastos_fijos = self._calcular_gastos_fijos_mensuales()
            if gastos_fijos > 0:
                cobertura = datos_actuales['ingresos_mes'] / gastos_fijos
                indicadores['cobertura_gastos_fijos'] = {
                    'valor': round(cobertura, 1),
                    'riesgo': 'Alto' if cobertura < 1.2 else 'Medio' if cobertura < 2.0 else 'Bajo',
                    'descripcion': 'Veces que los ingresos cubren gastos fijos'
                }
            
            # Calcular riesgo general
            riesgo_general = self._calcular_riesgo_general(indicadores)
            
            # Tiempo estimado hasta problemas críticos
            tiempo_critico = self._estimar_tiempo_hasta_crisis(datos_actuales, indicadores)
            
            return {
                'success': True,
                'riesgo_general': riesgo_general,
                'indicadores': indicadores,
                'tiempo_critico': tiempo_critico,
                'recomendaciones_urgentes': self._generar_recomendaciones_riesgo(riesgo_general, indicadores),
                'plan_contingencia': self._generar_plan_contingencia(riesgo_general)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Error detectando riesgo de quiebra: {str(e)}'}
    
    def predecir_demanda_productos(self, meses=3):
        """Predice demanda de productos para optimizar inventario"""
        try:
            productos = Producto.objects.filter(empresa=self.empresa)
            predicciones_productos = []
            
            for producto in productos[:20]:  # Limitar a 20 productos principales
                # Obtener historial de ventas del producto
                ventas_historicas = self._obtener_ventas_producto_historicas(producto, 6)  # 6 meses
                
                if len(ventas_historicas) < 2:
                    continue
                
                # Calcular tendencia de demanda
                cantidades = [v['cantidad_total'] for v in ventas_historicas]
                tendencia = self._calcular_tendencia(cantidades)
                
                # Calcular estacionalidad
                promedio_mensual = sum(cantidades) / len(cantidades)
                
                # Predicciones por mes
                predicciones_mes = []
                for i in range(meses):
                    demanda_base = cantidades[-1] + (tendencia * (i + 1))
                    demanda_predicha = max(0, demanda_base)
                    
                    # Calcular stock recomendado (demanda + stock de seguridad)
                    stock_seguridad = demanda_predicha * 0.2  # 20% de stock de seguridad
                    stock_recomendado = demanda_predicha + stock_seguridad
                    
                    predicciones_mes.append({
                        'mes': i + 1,
                        'demanda_predicha': round(demanda_predicha),
                        'stock_recomendado': round(stock_recomendado),
                        'necesidad_compra': max(0, round(stock_recomendado - producto.stock))
                    })
                
                predicciones_productos.append({
                    'producto': producto.nombre,
                    'stock_actual': producto.stock,
                    'promedio_mensual': round(promedio_mensual),
                    'tendencia': round(tendencia, 1),
                    'predicciones': predicciones_mes,
                    'prioridad': self._calcular_prioridad_restock(producto, predicciones_mes[0])
                })
            
            # Ordenar por prioridad
            predicciones_productos.sort(key=lambda x: x['prioridad'], reverse=True)
            
            return {
                'success': True,
                'predicciones_productos': predicciones_productos,
                'resumen_compras': self._generar_resumen_compras_recomendadas(predicciones_productos),
                'inversion_requerida': self._calcular_inversion_requerida(predicciones_productos)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Error prediciendo demanda: {str(e)}'}
    
    def predecir_rentabilidad_futura(self, escenarios=['optimista', 'realista', 'pesimista']):
        """Predice rentabilidad futura bajo diferentes escenarios"""
        try:
            # Obtener datos base
            datos_base = self._obtener_datos_rentabilidad_base()
            
            predicciones_escenarios = {}
            
            for escenario in escenarios:
                # Definir factores de ajuste por escenario
                factores = self._obtener_factores_escenario(escenario)
                
                # Calcular predicciones para 6 meses
                predicciones_meses = []
                
                for mes in range(1, 7):
                    # Aplicar factores de crecimiento/decrecimiento
                    ventas_predichas = datos_base['ventas_promedio'] * factores['crecimiento_ventas'] ** mes
                    costos_predichos = datos_base['costos_promedio'] * factores['crecimiento_costos'] ** mes
                    gastos_predichos = datos_base['gastos_promedio'] * factores['crecimiento_gastos'] ** mes
                    
                    # Calcular rentabilidad
                    utilidad_bruta = ventas_predichas - costos_predichos
                    utilidad_neta = utilidad_bruta - gastos_predichos
                    margen_neto = (utilidad_neta / ventas_predichas * 100) if ventas_predichas > 0 else 0
                    
                    predicciones_meses.append({
                        'mes': mes,
                        'ventas': round(ventas_predichas, 2),
                        'costos': round(costos_predichos, 2),
                        'gastos': round(gastos_predichos, 2),
                        'utilidad_bruta': round(utilidad_bruta, 2),
                        'utilidad_neta': round(utilidad_neta, 2),
                        'margen_neto': round(margen_neto, 1)
                    })
                
                predicciones_escenarios[escenario] = {
                    'predicciones': predicciones_meses,
                    'utilidad_total_6_meses': sum(p['utilidad_neta'] for p in predicciones_meses),
                    'margen_promedio': sum(p['margen_neto'] for p in predicciones_meses) / len(predicciones_meses)
                }
            
            # Análisis comparativo
            analisis_comparativo = self._generar_analisis_comparativo_escenarios(predicciones_escenarios)
            
            return {
                'success': True,
                'predicciones_escenarios': predicciones_escenarios,
                'analisis_comparativo': analisis_comparativo,
                'recomendaciones_estrategicas': self._generar_recomendaciones_estrategicas(predicciones_escenarios)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Error prediciendo rentabilidad: {str(e)}'}
    
    def _obtener_datos_flujo_historico(self, meses):
        """Obtiene datos históricos de flujo de caja"""
        datos = []
        fecha_fin = date.today()
        
        for i in range(meses):
            # Calcular fecha del mes
            if fecha_fin.month - i <= 0:
                mes = 12 + (fecha_fin.month - i)
                año = fecha_fin.year - 1
            else:
                mes = fecha_fin.month - i
                año = fecha_fin.year
            
            # Obtener ingresos del mes
            ingresos = Venta.objects.filter(
                empresa=self.empresa,
                fecha__year=año,
                fecha__month=mes
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            # Obtener egresos del mes
            egresos = Gasto.objects.filter(
                empresa=self.empresa,
                fecha__year=año,
                fecha__month=mes
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            # Agregar compras
            compras = Compra.objects.filter(
                empresa=self.empresa,
                fecha__year=año,
                fecha__month=mes
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            egresos += compras
            
            datos.insert(0, {  # Insertar al inicio para orden cronológico
                'mes': mes,
                'año': año,
                'ingresos': float(ingresos),
                'egresos': float(egresos),
                'flujo_neto': float(ingresos - egresos)
            })
        
        return datos
    
    def _calcular_tendencia(self, valores):
        """Calcula tendencia lineal de una serie de valores"""
        if len(valores) < 2:
            return 0
        
        n = len(valores)
        x = list(range(n))
        
        # Calcular pendiente usando mínimos cuadrados
        sum_x = sum(x)
        sum_y = sum(valores)
        sum_xy = sum(x[i] * valores[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        if n * sum_x2 - sum_x ** 2 == 0:
            return 0
        
        pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return pendiente
    
    def _calcular_estacionalidad(self, valores):
        """Calcula factores estacionales por mes"""
        if len(valores) < 12:
            return {i: 1.0 for i in range(1, 13)}
        
        # Calcular promedio general
        promedio_general = sum(valores) / len(valores)
        
        # Calcular factor estacional por mes
        factores = {}
        for i in range(12):
            if i < len(valores):
                factor = valores[i] / promedio_general if promedio_general > 0 else 1.0
                factores[i + 1] = max(0.5, min(2.0, factor))  # Limitar entre 0.5 y 2.0
            else:
                factores[i + 1] = 1.0
        
        return factores
    
    def _obtener_saldo_actual(self):
        """Obtiene saldo actual de caja"""
        try:
            # Calcular saldo aproximado desde movimientos
            ingresos_total = Venta.objects.filter(empresa=self.empresa).aggregate(
                total=Sum('monto'))['total'] or 0
            egresos_total = Gasto.objects.filter(empresa=self.empresa).aggregate(
                total=Sum('monto'))['total'] or 0
            compras_total = Compra.objects.filter(empresa=self.empresa).aggregate(
                total=Sum('monto'))['total'] or 0
            return float(ingresos_total - egresos_total - compras_total)
        except:
            return 1000  # Saldo por defecto
    
    def _prediccion_flujo_simple(self, meses):
        """Predicción simple cuando hay pocos datos"""
        # Obtener promedios de los últimos 3 meses
        fecha_inicio = date.today() - timedelta(days=90)
        
        ingresos_promedio = Venta.objects.filter(
            empresa=self.empresa,
            fecha__gte=fecha_inicio
        ).aggregate(total=Sum('monto'))['total'] or 0
        ingresos_promedio = ingresos_promedio / 3
        
        egresos_promedio = Gasto.objects.filter(
            empresa=self.empresa,
            fecha__gte=fecha_inicio
        ).aggregate(total=Sum('monto'))['total'] or 0
        egresos_promedio = egresos_promedio / 3
        
        predicciones = []
        saldo_actual = self._obtener_saldo_actual()
        
        for i in range(meses):
            flujo_neto = ingresos_promedio - egresos_promedio
            saldo_final = saldo_actual + flujo_neto
            
            predicciones.append({
                'mes': i + 1,
                'ingresos_predichos': round(ingresos_promedio, 2),
                'egresos_predichos': round(egresos_promedio, 2),
                'flujo_neto': round(flujo_neto, 2),
                'saldo_inicial': round(saldo_actual, 2),
                'saldo_final': round(saldo_final, 2),
                'riesgo_liquidez': 'Alto' if saldo_final < 0 else 'Bajo'
            })
            
            saldo_actual = saldo_final
        
        return {
            'success': True,
            'predicciones': predicciones,
            'metodo': 'Promedio simple',
            'confianza': 'Baja'
        }
    
    def _obtener_datos_financieros_actuales(self):
        """Obtiene datos financieros actuales para análisis de riesgo"""
        # Implementación simplificada
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        
        ingresos_mes = Venta.objects.filter(
            empresa=self.empresa,
            fecha__gte=inicio_mes
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        gastos_mes = Gasto.objects.filter(
            empresa=self.empresa,
            fecha__gte=inicio_mes
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        return {
            'activos_corrientes': 10000,  # Simplificado
            'pasivos_corrientes': 5000,
            'activos_totales': 15000,
            'pasivos_totales': 7000,
            'ingresos_mes': float(ingresos_mes),
            'gastos_operativos': float(gastos_mes)
        }
    
    def _calcular_riesgo_general(self, indicadores):
        """Calcula riesgo general basado en indicadores"""
        riesgos_altos = sum(1 for ind in indicadores.values() if ind.get('riesgo') == 'Alto')
        total_indicadores = len(indicadores)
        
        if riesgos_altos >= total_indicadores * 0.6:
            return 'Alto'
        elif riesgos_altos >= total_indicadores * 0.3:
            return 'Medio'
        else:
            return 'Bajo'
    
    def _generar_recomendaciones_flujo(self, predicciones):
        """Genera recomendaciones basadas en predicciones de flujo"""
        recomendaciones = []
        
        # Verificar meses con flujo negativo
        meses_negativos = [p for p in predicciones if p['flujo_neto'] < 0]
        if meses_negativos:
            recomendaciones.append("Implementar estrategias para mejorar flujo de caja en meses críticos")
        
        # Verificar saldos bajos
        saldos_bajos = [p for p in predicciones if p['saldo_final'] < 1000]
        if saldos_bajos:
            recomendaciones.append("Establecer línea de crédito para emergencias de liquidez")
        
        return recomendaciones
    
    def _calcular_confianza_prediccion(self, meses_datos):
        """Calcula nivel de confianza de la predicción"""
        if meses_datos >= 12:
            return 'Alta'
        elif meses_datos >= 6:
            return 'Media'
        else:
            return 'Baja'