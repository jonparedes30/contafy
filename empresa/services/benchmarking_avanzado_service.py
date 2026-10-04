"""
Benchmarking Avanzado con ValuaciÃ³n y AnÃ¡lisis Predictivo
Integra: comparaciÃ³n sectorial + valuaciÃ³n + proyecciones + anÃ¡lisis de riesgo
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

        # Proyecciones — ahora retorna dict con escenarios
        proyecciones_dict = BenchmarkingAvanzadoService._proyectar_posicion_futura(empresa)

        # Combinar todo
        return {
            **benchmarking_base,
            'valuacion_comparativa': valuacion_comparativa,
            'analisis_predictivo': analisis_predictivo,
            # Mantener compat: 'proyecciones_posicion' sigue siendo lista plana (escenario base)
            'proyecciones_posicion': proyecciones_dict['base'],
            # Nuevo: dict completo con escenarios + metadata
            'proyecciones_escenarios': {
                'conservador': proyecciones_dict['conservador'],
                'base':        proyecciones_dict['base'],
                'optimista':   proyecciones_dict['optimista'],
                'nota':        proyecciones_dict['nota'],
                'calidad_datos': proyecciones_dict['calidad_datos'],
                'tiene_historico': proyecciones_dict['tiene_historico'],
                'tasa_base_aplicada': proyecciones_dict['tasa_base_aplicada'],
            },
            'tamano_empresa': BenchmarkingAvanzadoService._clasificar_tamano_empresa(empresa)
        }
    
    # Múltiplos de valuación por sector (basados en rangos típicos de mercado).
    # Fix #5: en lugar de un múltiplo universal (2x ventas + 10x utilidad),
    # se ajusta según la categoría de la empresa.
    MULTIPLOS_SECTOR = {
        'comercial':  {'ventas': 0.8, 'utilidad': 8.0, 'minimo_ventas': 0.3},
        'manufactura': {'ventas': 1.0, 'utilidad': 10.0, 'minimo_ventas': 0.4},
        'servicios':  {'ventas': 1.5, 'utilidad': 8.0,  'minimo_ventas': 0.5},
        # default conservador si no se reconoce el sector
        '_default':   {'ventas': 1.0, 'utilidad': 8.0,  'minimo_ventas': 0.4},
    }

    @staticmethod
    def _calcular_valuacion_comparativa(empresa):
        """Calcula valuación y la compara con el sector"""

        # Datos financieros propios
        datos_propios = BenchmarkingAvanzadoService._obtener_datos_financieros(empresa)

        # Valuación propia (multiplicadores por sector)
        valuacion_propia = BenchmarkingAvanzadoService._calcular_valuacion_simple(
            datos_propios, empresa.categoria
        )

        # Obtener empresas similares para comparar valuación
        empresas_similares = Empresa.objects.filter(
            categoria=empresa.categoria
        ).exclude(id=empresa.id)

        valuaciones_sector = []
        for emp in empresas_similares:
            datos_emp = BenchmarkingAvanzadoService._obtener_datos_financieros(emp)
            if datos_emp['ventas_anuales'] > 0:
                valuacion_emp = BenchmarkingAvanzadoService._calcular_valuacion_simple(
                    datos_emp, emp.categoria
                )
                valuaciones_sector.append(valuacion_emp)

        if len(valuaciones_sector) >= 3:
            valuacion_promedio_sector = sum(valuaciones_sector) / len(valuaciones_sector)
            valuaciones_ordenadas = sorted(valuaciones_sector)
            valuacion_mediana_sector = valuaciones_ordenadas[len(valuaciones_ordenadas)//2]

            # Percentil real (no aproximado) usando bisect para precisión
            import bisect
            posicion = bisect.bisect_left(valuaciones_ordenadas, valuacion_propia)
            percentil_valuacion = (posicion / len(valuaciones_ordenadas)) * 100

            return {
                'valuacion_propia': valuacion_propia,
                'valuacion_promedio_sector': valuacion_promedio_sector,
                'valuacion_mediana_sector': valuacion_mediana_sector,
                'percentil_valuacion': round(percentil_valuacion, 1),
                'total_empresas_comparadas': len(valuaciones_sector),
                'multiplos_aplicados': BenchmarkingAvanzadoService.MULTIPLOS_SECTOR.get(
                    empresa.categoria,
                    BenchmarkingAvanzadoService.MULTIPLOS_SECTOR['_default']
                ),
                'tiene_datos': True
            }

        return {'tiene_datos': False, 'razon': 'Datos insuficientes para comparación de valuación (mínimo 3 empresas similares)'}

    @staticmethod
    def _calcular_valuacion_simple(datos, categoria='_default'):
        """
        Valuación simplificada con múltiplos ajustados por sector (fix #5).

        Fórmula:
            valuacion = ventas * múltiplo_ventas + utilidad * múltiplo_utilidad (si > 0)
            valuacion_mínima = ventas * múltiplo_mínimo_ventas

        Args:
            datos: dict con 'ventas_anuales' y 'utilidad_neta'
            categoria: 'comercial', 'manufactura', 'servicios' o '_default'
        """
        mult = BenchmarkingAvanzadoService.MULTIPLOS_SECTOR.get(
            categoria, BenchmarkingAvanzadoService.MULTIPLOS_SECTOR['_default']
        )

        ventas = datos['ventas_anuales']
        utilidad = datos['utilidad_neta']

        valuacion = ventas * mult['ventas']
        if utilidad > 0:
            valuacion += utilidad * mult['utilidad']

        # Piso mínimo según sector
        valuacion = max(valuacion, ventas * mult['minimo_ventas'])
        return valuacion
    
    @staticmethod
    def _calcular_analisis_predictivo(empresa):
        """Análisis predictivo de riesgo y oportunidades"""
        datos = BenchmarkingAvanzadoService._obtener_datos_financieros(empresa)

        z_score = BenchmarkingAvanzadoService._calcular_altman_z_score(datos)
        score_crecimiento = BenchmarkingAvanzadoService._calcular_probabilidad_crecimiento(datos)
        alertas = BenchmarkingAvanzadoService._generar_alertas_tempranas(datos)

        return {
            'z_score': z_score,
            'riesgo_quiebra': BenchmarkingAvanzadoService._interpretar_z_score(z_score),
            # Mantener el key 'probabilidad_crecimiento' por compatibilidad con templates,
            # pero agregar el alias 'score_crecimiento' que refleja mejor su naturaleza.
            'probabilidad_crecimiento': score_crecimiento,
            'score_crecimiento': score_crecimiento,
            'alertas_tempranas': alertas,
            'tendencia_general': BenchmarkingAvanzadoService._evaluar_tendencia_general(datos)
        }
    
    @staticmethod
    def _calcular_altman_z_score(datos):
        """
        Altman Z'-Score (1983) adaptado para PYMEs no cotizadas, ajustado a los
        ratios disponibles en el sistema (sin utilidades retenidas separadas ni
        valor de mercado del patrimonio).

        Fórmula completa (Z'-Score):
            Z' = 0.717 * (WC/TA)          ← capital trabajo / activos
               + 0.847 * (RE/TA)          ← utilidades retenidas / activos
               + 3.107 * (EBIT/TA)        ← util. operativa / activos
               + 0.420 * (BVE/TL)         ← patrimonio libros / pasivos
               + 0.998 * (Sales/TA)       ← ventas / activos

        Como no separamos utilidades retenidas, las aproximamos con la utilidad
        operativa del período. El componente BVE/TL se aproxima con (TA−TL)/TL.

        Umbrales Z'-Score Altman 1983:
            > 2.90  → Zona segura
            1.23 – 2.90 → Zona gris
            < 1.23  → Zona de quiebra
        """
        TA = datos['activos_totales']
        TL = datos['pasivos_totales']
        if TA == 0:
            return 0

        capital_trabajo = TA - TL
        EBIT = datos.get('utilidad_operativa', datos['utilidad_neta'])
        equity_libros = TA - TL  # patrimonio según libros

        wc_ta = capital_trabajo / TA
        re_ta = (EBIT * 0.5) / TA              # proxy utilidades retenidas ≈ 50% EBIT acumulado
        ebit_ta = EBIT / TA
        bve_tl = (equity_libros / TL) if TL > 0 else 4.0  # cap a 4 si no hay pasivos
        sales_ta = datos['ventas_anuales'] / TA

        z_score = (
            0.717 * wc_ta
            + 0.847 * re_ta
            + 3.107 * ebit_ta
            + 0.420 * min(bve_tl, 4.0)   # cap evita Z infinito si TL=0
            + 0.998 * sales_ta
        )

        return round(z_score, 2)

    @staticmethod
    def _interpretar_z_score(z_score):
        """
        Interpretación del Z'-Score (Altman 1983) para PYMEs no cotizadas.
        Umbrales oficiales: zona segura >2.90, zona gris 1.23–2.90, quiebra <1.23.
        """
        if z_score > 2.90:
            return {'nivel': 'Bajo', 'descripcion': 'Zona segura — empresa financieramente sólida'}
        elif z_score > 1.23:
            return {'nivel': 'Medio', 'descripcion': 'Zona gris — situación financiera estable pero monitorear'}
        else:
            return {'nivel': 'Alto', 'descripcion': 'Zona de riesgo — requiere atención financiera urgente'}
    
    @staticmethod
    def _calcular_probabilidad_crecimiento(datos):
        """
        Calcula un SCORE (0-100) de potencial de crecimiento.

        Nota: este NO es una probabilidad estadística real, es un score heurístico
        basado en 4 factores ponderados (fix #12 — antes se llamaba "probabilidad"
        lo cual confundía a usuarios pensando que era una probabilidad real).

        Factores y pesos:
            - Rentabilidad (margen neto): 30 puntos
            - Crecimiento histórico:      25 puntos
            - Liquidez (solvencia):       20 puntos
            - Tamaño (ventas anuales):    25 puntos
            Total máximo: 100 puntos
        """
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

        # Factor liquidez (solvencia)
        if datos['activos_totales'] > datos['pasivos_totales'] * 1.5:
            factores.append(20)
        else:
            factores.append(10)

        # Factor tamaño (ventas anuales)
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
        """EvalÃºa la tendencia general de la empresa"""
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
        """
        Proyecta la posición futura con 3 escenarios (conservador/base/optimista)
        y factor de decaimiento aplicado a cada uno.

        Mejoras sobre versión anterior:
        - Si hay datos históricos: escenarios = base ± 5%
        - Si no hay datos (tasa=0): usa tasas sectoriales típicas (3%/8%/15%)
        - Decaimiento del crecimiento (0.7^año) — regresión hacia el promedio
        - Indicador `calidad_datos` para que el frontend muestre confianza

        Esto soluciona el problema visual de "proyección plana" cuando la empresa
        no tiene historial — antes mostraba mismos valores todos los años.
        """
        datos = BenchmarkingAvanzadoService._obtener_datos_financieros(empresa)
        ventas_base = datos['ventas_anuales']
        utilidad_base = datos['utilidad_neta']
        tasa_real = max(-50.0, min(50.0, datos['tasa_crecimiento']))

        # Detectar si hay datos históricos suficientes
        tiene_historico = tasa_real != 0 and ventas_base > 0
        calidad_datos = 'alta' if tiene_historico else 'baja'

        if tiene_historico:
            # Escenarios basados en la tasa real de la empresa
            tasa_conservadora = max(tasa_real - 5.0, -50.0)
            tasa_base = tasa_real
            tasa_optimista = min(tasa_real + 5.0, 50.0)
            nota = 'Proyecciones basadas en el crecimiento histórico de tu empresa'
        else:
            # Sin datos históricos: usar tasas sectoriales típicas como referencia
            # (basadas en estadísticas del SRI y BCE para PYMEs ecuatorianas)
            tasa_conservadora = 3.0   # crecimiento al ritmo de inflación esperada
            tasa_base = 8.0           # crecimiento moderado típico del sector
            tasa_optimista = 15.0     # crecimiento ambicioso pero alcanzable
            nota = 'Proyecciones estimadas con tasas sectoriales típicas (faltan datos históricos de tu empresa)'

        def _posicion_para(ventas):
            """Clasificación según SRI Ecuador (coherente con _clasificar_tamano_empresa)."""
            if ventas > 5_000_000:
                return 'Grande (Top 1%)'
            elif ventas > 1_000_000:
                return 'Mediana (Top 10%)'
            elif ventas > 100_000:
                return 'Pequeña (Top 30%)'
            else:
                return 'Microempresa'

        def _proyectar_escenario(tasa_pct):
            """Genera 3 años con decaimiento del 30% anual del crecimiento."""
            crecimiento = tasa_pct / 100
            resultado = []
            for anio in range(1, 4):
                decay = 0.7 ** (anio - 1)
                crecimiento_efectivo = crecimiento * decay
                factor = (1 + crecimiento_efectivo) ** anio

                ventas_proy = ventas_base * factor
                # Para escenario sin datos históricos, utilidad proporcional
                if utilidad_base != 0:
                    utilidad_proy = utilidad_base * factor
                else:
                    # Estima utilidad usando margen sectorial típico (10%)
                    utilidad_proy = ventas_proy * 0.10

                resultado.append({
                    'anio': anio,
                    'ventas_proyectadas': round(ventas_proy, 2),
                    'utilidad_proyectada': round(utilidad_proy, 2),
                    'tasa_crecimiento_efectiva': round(crecimiento_efectivo * 100, 1),
                    'posicion_estimada': _posicion_para(ventas_proy),
                })
            return resultado

        return {
            'calidad_datos': calidad_datos,
            'nota': nota,
            'tiene_historico': tiene_historico,
            'tasa_base_aplicada': tasa_base,
            # Escenarios
            'conservador': _proyectar_escenario(tasa_conservadora),
            'base': _proyectar_escenario(tasa_base),
            'optimista': _proyectar_escenario(tasa_optimista),
            # Mantener compatibilidad con templates antiguos (key 'proyecciones_posicion')
            # devuelve el escenario base como lista plana
            '_proyecciones_legacy': _proyectar_escenario(tasa_base),
        }
    
    @staticmethod
    def _clasificar_tamano_empresa(empresa):
        """
        Clasifica el tamaño de la empresa según las definiciones oficiales
        del SRI Ecuador (Reglamento LRTI Art. 75):
            - Microempresa:   ingresos anuales hasta $100,000
            - Pequeña:        $100,001 a $1,000,000
            - Mediana:        $1,000,001 a $5,000,000
            - Grande:         $5,000,001 en adelante

        Fix #11: reemplaza los umbrales arbitrarios anteriores ($500K = grande)
        con los oficiales del SRI Ecuador.
        """
        datos = BenchmarkingAvanzadoService._obtener_datos_financieros(empresa)
        ventas = datos['ventas_anuales']

        if ventas > 5_000_000:
            return {'categoria': 'Grande', 'descripcion': 'Empresa grande (>$5M ingresos anuales — SRI Ecuador)'}
        elif ventas > 1_000_000:
            return {'categoria': 'Mediana', 'descripcion': 'Empresa mediana ($1M-$5M — SRI Ecuador)'}
        elif ventas > 100_000:
            return {'categoria': 'Pequeña', 'descripcion': 'Pequeña empresa ($100K-$1M — SRI Ecuador)'}
        else:
            return {'categoria': 'Micro', 'descripcion': 'Microempresa (<$100K — SRI Ecuador)'}
    
    @staticmethod
    def _obtener_datos_financieros(empresa):
        """
        Obtiene datos financieros usando los modelos Venta/Compra/Gasto directos
        (más robusto que buscar cuentas por nombre exacto, ver fix #4 del audit).

        Utilidad calculada según fórmula NIIF (fix #1):
            utilidad = ventas_netas − costo_ventas (compras) − gastos_operativos
        """
        from empresa.models import Venta, Compra, Gasto
        hoy = timezone.now()
        hace_12_meses = hoy - timedelta(days=365)
        hace_6_meses = hoy - timedelta(days=180)

        # ─── Ventas netas (sin IVA), últimos 12 meses ───────────
        ventas_qs_12m = Venta.objects.filter(empresa=empresa, fecha__gte=hace_12_meses)
        ventas_anuales = (ventas_qs_12m.aggregate(t=Sum('monto_neto'))['t']
                          or ventas_qs_12m.aggregate(t=Sum('monto'))['t'] or 0)

        # Ventas recientes (últimos 6 meses) vs anteriores (6-12 meses)
        ventas_qs_recientes = Venta.objects.filter(empresa=empresa, fecha__gte=hace_6_meses)
        ventas_recientes = (ventas_qs_recientes.aggregate(t=Sum('monto_neto'))['t']
                            or ventas_qs_recientes.aggregate(t=Sum('monto'))['t'] or 0)

        ventas_qs_anteriores = Venta.objects.filter(
            empresa=empresa, fecha__gte=hace_12_meses, fecha__lt=hace_6_meses
        )
        ventas_anteriores = (ventas_qs_anteriores.aggregate(t=Sum('monto_neto'))['t']
                             or ventas_qs_anteriores.aggregate(t=Sum('monto'))['t'] or 0)

        # ─── Costo de ventas (compras de inventario), 12 meses ──
        compras_qs = Compra.objects.filter(empresa=empresa, fecha__gte=hace_12_meses)
        costo_ventas_anual = (compras_qs.aggregate(t=Sum('monto_neto'))['t']
                              or compras_qs.aggregate(t=Sum('monto'))['t'] or 0)

        # ─── Gastos operativos, 12 meses ────────────────────────
        gastos_anuales = Gasto.objects.filter(
            empresa=empresa, fecha__gte=hace_12_meses
        ).aggregate(t=Sum('monto'))['t'] or 0

        # ─── Activos y pasivos (siguen usando MovimientoContable) ─
        cuentas_activos = CuentaContable.objects.filter(empresa=empresa, tipo='activo')
        activos_totales = sum(cuenta.valor for cuenta in cuentas_activos)

        cuentas_pasivos = CuentaContable.objects.filter(empresa=empresa, tipo='pasivo')
        pasivos_totales = sum(cuenta.valor for cuenta in cuentas_pasivos)

        # ─── Cálculos derivados (NIIF) ─────────────────────────
        # Utilidad operativa (proxy de EBIT): ventas − costo − gastos
        utilidad_operativa = float(ventas_anuales) - float(costo_ventas_anual) - float(gastos_anuales)
        # Utilidad neta = utilidad operativa (sin descontar impuestos en benchmarking)
        utilidad_neta = utilidad_operativa

        # Tasa de crecimiento con cap (fix #6: evitar % absurdos)
        if float(ventas_anteriores) > 0:
            tasa_crecimiento = ((float(ventas_recientes) - float(ventas_anteriores))
                                / float(ventas_anteriores) * 100)
            # Cap: -90% a +500% (más allá no es realista para análisis)
            tasa_crecimiento = max(-90.0, min(500.0, tasa_crecimiento))
        else:
            tasa_crecimiento = 0

        margen_neto = (utilidad_neta / float(ventas_anuales) * 100) if float(ventas_anuales) > 0 else 0

        return {
            'ventas_anuales': float(ventas_anuales),
            'costo_ventas_anual': float(costo_ventas_anual),
            'gastos_anuales': float(gastos_anuales),
            'utilidad_operativa': float(utilidad_operativa),
            'utilidad_neta': float(utilidad_neta),
            'activos_totales': float(activos_totales),
            'pasivos_totales': float(pasivos_totales),
            'tasa_crecimiento': float(tasa_crecimiento),
            'margen_neto': float(margen_neto),
        }

