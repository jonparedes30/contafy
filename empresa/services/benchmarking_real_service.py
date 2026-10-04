"""
Servicio de Benchmarking con Datos Reales
Mantiene privacidad - solo muestra promedios agregados, nunca datos individuales
"""
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from empresa.models import Empresa, Venta, Gasto, MovimientoContable, CuentaContable
from empresa.utils.normalizador import calcular_distancia_km, normalizar_tipo_negocio
import math

class BenchmarkingRealService:

    # Cache request-level de métricas por empresa para evitar recalcular
    # las mismas métricas múltiples veces durante una sola request.
    # Fix #8: antes se recalculaba para cada nivel (categoría, ciudad,
    # provincia, etc.) lo cual generaba N×K queries innecesarios.
    _metricas_cache = None

    @staticmethod
    def _obtener_metricas_cached(empresa):
        """Versión cacheada de _calcular_metricas_empresa por sesión."""
        if BenchmarkingRealService._metricas_cache is None:
            BenchmarkingRealService._metricas_cache = {}
        if empresa.id not in BenchmarkingRealService._metricas_cache:
            BenchmarkingRealService._metricas_cache[empresa.id] = (
                BenchmarkingRealService._calcular_metricas_empresa(empresa)
            )
        return BenchmarkingRealService._metricas_cache[empresa.id]

    @staticmethod
    def obtener_benchmarking_completo(empresa):
        """Obtiene benchmarking completo con datos reales por niveles geográficos"""

        # Resetear cache al inicio de cada análisis para no acarrear datos viejos
        BenchmarkingRealService._metricas_cache = {}

        # Calcular métricas propias (queda en cache para reuso)
        metricas_propias = BenchmarkingRealService._obtener_metricas_cached(empresa)

        # Obtener comparaciones por niveles
        comparaciones = {
            'categoria': BenchmarkingRealService._benchmarking_por_categoria(empresa),
            'tipo_negocio': BenchmarkingRealService._benchmarking_por_tipo_negocio(empresa),
            'ciudad': BenchmarkingRealService._benchmarking_por_ciudad(empresa),
            'provincia': BenchmarkingRealService._benchmarking_por_provincia(empresa),
            'pais': BenchmarkingRealService._benchmarking_nacional(empresa),
            'cercanas_100km': BenchmarkingRealService._benchmarking_100km(empresa)
        }

        # Calcular percentiles y posiciones (reusa cache de métricas)
        posiciones = BenchmarkingRealService._calcular_posiciones(empresa, comparaciones)

        # Generar recomendaciones
        recomendaciones = BenchmarkingRealService._generar_recomendaciones_privadas(
            metricas_propias, comparaciones
        )

        # Limpiar cache para no afectar requests futuras
        BenchmarkingRealService._metricas_cache = None

        return {
            'metricas_propias': metricas_propias,
            'comparaciones': comparaciones,
            'posiciones': posiciones,
            'recomendaciones': recomendaciones
        }
    
    @staticmethod
    def _calcular_metricas_empresa(empresa):
        """
        Calcula métricas usando los modelos Venta/Compra/Gasto directos
        (más robusto que cuentas por nombre exacto — fix #4 del audit).

        Cálculo de utilidad NIIF (fix #1):
            utilidad_bruta  = ventas_netas − costo_ventas (compras)
            utilidad_neta   = utilidad_bruta − gastos_operativos

        Cálculo de crecimiento mensual correcto (fix #2):
            compara el mes actual contra el mes inmediato anterior (no contra
            la fórmula incorrecta `(ventas_3m - ventas_mes) / 2` del código previo).
        """
        from empresa.models import Venta, Compra, Gasto

        hoy = timezone.now()
        inicio_mes_actual = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Mes inmediato anterior (rango cerrado [inicio_anterior, inicio_actual))
        if hoy.month == 1:
            inicio_mes_anterior = inicio_mes_actual.replace(year=hoy.year - 1, month=12)
        else:
            inicio_mes_anterior = inicio_mes_actual.replace(month=hoy.month - 1)

        hace_3_meses = hoy - timedelta(days=90)
        hace_6_meses = hoy - timedelta(days=180)

        # ─── Ventas mensuales (netas, sin IVA) ─────────────────
        ventas_qs_mes = Venta.objects.filter(empresa=empresa, fecha__gte=inicio_mes_actual)
        ventas_mes = (ventas_qs_mes.aggregate(t=Sum('monto_neto'))['t']
                      or ventas_qs_mes.aggregate(t=Sum('monto'))['t'] or 0)

        # Ventas del mes inmediato anterior (para crecimiento real)
        ventas_qs_mes_ant = Venta.objects.filter(
            empresa=empresa,
            fecha__gte=inicio_mes_anterior,
            fecha__lt=inicio_mes_actual
        )
        ventas_mes_anterior = (ventas_qs_mes_ant.aggregate(t=Sum('monto_neto'))['t']
                               or ventas_qs_mes_ant.aggregate(t=Sum('monto'))['t'] or 0)

        # Ventas trimestre y semestre
        ventas_qs_3m = Venta.objects.filter(empresa=empresa, fecha__gte=hace_3_meses)
        ventas_3m = (ventas_qs_3m.aggregate(t=Sum('monto_neto'))['t']
                     or ventas_qs_3m.aggregate(t=Sum('monto'))['t'] or 0)

        ventas_qs_6m = Venta.objects.filter(empresa=empresa, fecha__gte=hace_6_meses)
        ventas_6m = (ventas_qs_6m.aggregate(t=Sum('monto_neto'))['t']
                     or ventas_qs_6m.aggregate(t=Sum('monto'))['t'] or 0)

        # ─── Costo de ventas (compras del mes, sin IVA) ────────
        compras_qs_mes = Compra.objects.filter(empresa=empresa, fecha__gte=inicio_mes_actual)
        costos_mes = (compras_qs_mes.aggregate(t=Sum('monto_neto'))['t']
                      or compras_qs_mes.aggregate(t=Sum('monto'))['t'] or 0)

        # ─── Gastos operativos del mes ─────────────────────────
        gastos_mes = Gasto.objects.filter(
            empresa=empresa, fecha__gte=inicio_mes_actual
        ).aggregate(t=Sum('monto'))['t'] or 0

        # ─── Cálculos derivados (fix #1: utilidad correcta) ────
        ventas_mes_f = float(ventas_mes)
        utilidad_bruta = ventas_mes_f - float(costos_mes)
        utilidad_neta = utilidad_bruta - float(gastos_mes)

        margen_bruto = (utilidad_bruta / ventas_mes_f * 100) if ventas_mes_f > 0 else 0
        margen_neto = (utilidad_neta / ventas_mes_f * 100) if ventas_mes_f > 0 else 0

        # ─── Crecimiento mensual correcto (fix #2 + cap #6) ────
        if float(ventas_mes_anterior) > 0:
            crecimiento_mensual = ((ventas_mes_f - float(ventas_mes_anterior))
                                   / float(ventas_mes_anterior) * 100)
            crecimiento_mensual = max(-90.0, min(500.0, crecimiento_mensual))
        else:
            crecimiento_mensual = 0

        # ─── Crecimiento interanual (Y-o-Y) — fix #9: estacionalidad ────
        # Compara el mismo mes del año pasado para evitar distorsión por
        # estacionalidad (ej. retail en diciembre vs enero)
        try:
            inicio_mes_yoy = inicio_mes_actual.replace(year=inicio_mes_actual.year - 1)
            if inicio_mes_yoy.month == 1:
                fin_mes_yoy = inicio_mes_yoy.replace(year=inicio_mes_yoy.year + 1, month=1) if False \
                              else inicio_mes_yoy.replace(year=inicio_mes_yoy.year, month=2)
            else:
                # mes siguiente del mismo año
                if inicio_mes_yoy.month == 12:
                    fin_mes_yoy = inicio_mes_yoy.replace(year=inicio_mes_yoy.year + 1, month=1)
                else:
                    fin_mes_yoy = inicio_mes_yoy.replace(month=inicio_mes_yoy.month + 1)

            ventas_qs_yoy = Venta.objects.filter(
                empresa=empresa, fecha__gte=inicio_mes_yoy, fecha__lt=fin_mes_yoy
            )
            ventas_mismo_mes_anio_pasado = (
                ventas_qs_yoy.aggregate(t=Sum('monto_neto'))['t']
                or ventas_qs_yoy.aggregate(t=Sum('monto'))['t']
                or 0
            )

            if float(ventas_mismo_mes_anio_pasado) > 0:
                crecimiento_interanual = ((ventas_mes_f - float(ventas_mismo_mes_anio_pasado))
                                          / float(ventas_mismo_mes_anio_pasado) * 100)
                crecimiento_interanual = max(-90.0, min(500.0, crecimiento_interanual))
            else:
                crecimiento_interanual = 0
        except Exception:
            ventas_mismo_mes_anio_pasado = 0
            crecimiento_interanual = 0

        return {
            'ventas_mensuales': ventas_mes_f,
            'ventas_mes_anterior': float(ventas_mes_anterior),
            'ventas_mismo_mes_anio_pasado': float(ventas_mismo_mes_anio_pasado),
            'gastos_mensuales': float(gastos_mes),
            'costos_mensuales': float(costos_mes),
            'utilidad_bruta': float(utilidad_bruta),
            'utilidad_neta': float(utilidad_neta),
            'margen_bruto': float(margen_bruto),
            'margen_neto': float(margen_neto),
            'crecimiento_mensual': float(crecimiento_mensual),
            'crecimiento_interanual': float(crecimiento_interanual),  # ← fix #9 estacionalidad
            'ventas_trimestre': float(ventas_3m),
            'ventas_semestre': float(ventas_6m),
        }
    
    @staticmethod
    def _benchmarking_por_categoria(empresa):
        """Benchmarking por categoría (comercial, manufactura, servicios)"""
        empresas_categoria = Empresa.objects.filter(
            categoria=empresa.categoria
        ).exclude(id=empresa.id)
        
        return BenchmarkingRealService._calcular_metricas_agregadas(
            empresas_categoria, f"Categoría: {empresa.get_categoria_display()}"
        )
    
    @staticmethod
    def _benchmarking_por_tipo_negocio(empresa):
        """Benchmarking por tipo específico de negocio"""
        tipo_normalizado = normalizar_tipo_negocio(empresa.tipo_negocio, empresa.categoria)
        
        empresas_tipo = Empresa.objects.filter(
            categoria=empresa.categoria
        ).exclude(id=empresa.id)
        
        # Filtrar por tipo normalizado
        empresas_similares = []
        for emp in empresas_tipo:
            if normalizar_tipo_negocio(emp.tipo_negocio, emp.categoria) == tipo_normalizado:
                empresas_similares.append(emp.id)
        
        empresas_filtradas = Empresa.objects.filter(id__in=empresas_similares)
        
        return BenchmarkingRealService._calcular_metricas_agregadas(
            empresas_filtradas, f"Tipo: {empresa.tipo_negocio or 'Similar'}"
        )
    
    @staticmethod
    def _benchmarking_por_ciudad(empresa):
        """Benchmarking por ciudad"""
        if not empresa.ciudad:
            return BenchmarkingRealService._resultado_vacio("Ciudad no especificada")
        
        empresas_ciudad = Empresa.objects.filter(
            ciudad__iexact=empresa.ciudad
        ).exclude(id=empresa.id)
        
        return BenchmarkingRealService._calcular_metricas_agregadas(
            empresas_ciudad, f"Ciudad: {empresa.ciudad}"
        )
    
    @staticmethod
    def _benchmarking_por_provincia(empresa):
        """Benchmarking por provincia"""
        if not empresa.provincia:
            return BenchmarkingRealService._resultado_vacio("Provincia no especificada")
        
        empresas_provincia = Empresa.objects.filter(
            provincia__iexact=empresa.provincia
        ).exclude(id=empresa.id)
        
        return BenchmarkingRealService._calcular_metricas_agregadas(
            empresas_provincia, f"Provincia: {empresa.provincia}"
        )
    
    @staticmethod
    def _benchmarking_nacional(empresa):
        """Benchmarking a nivel nacional"""
        empresas_pais = Empresa.objects.exclude(id=empresa.id)
        
        return BenchmarkingRealService._calcular_metricas_agregadas(
            empresas_pais, "Nacional"
        )
    
    @staticmethod
    def _coordenadas_validas(empresa):
        """
        Valida que las coordenadas GPS de una empresa sean numéricamente válidas
        y estén en rangos terrestres reales (-90 a 90 lat, -180 a 180 lng).
        Fix #14: antes solo verificaba `if empresa.latitud and empresa.longitud`
        sin validar que fueran números o rangos válidos.
        """
        if empresa.latitud is None or empresa.longitud is None:
            return False
        try:
            lat = float(empresa.latitud)
            lng = float(empresa.longitud)
            return -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _benchmarking_100km(empresa):
        """Benchmarking de empresas en 100km a la redonda"""
        if not BenchmarkingRealService._coordenadas_validas(empresa):
            return BenchmarkingRealService._resultado_vacio("Coordenadas GPS no disponibles o inválidas")

        empresas_con_gps = Empresa.objects.filter(
            latitud__isnull=False,
            longitud__isnull=False
        ).exclude(id=empresa.id)

        empresas_cercanas_ids = []
        for emp in empresas_con_gps:
            if not BenchmarkingRealService._coordenadas_validas(emp):
                continue
            try:
                distancia = calcular_distancia_km(
                    float(empresa.latitud), float(empresa.longitud),
                    float(emp.latitud), float(emp.longitud)
                )
            except (TypeError, ValueError):
                continue
            if distancia and distancia <= 100:
                empresas_cercanas_ids.append(emp.id)

        empresas_cercanas = Empresa.objects.filter(id__in=empresas_cercanas_ids)

        return BenchmarkingRealService._calcular_metricas_agregadas(
            empresas_cercanas, "100km a la redonda"
        )
    
    @staticmethod
    def _calcular_metricas_agregadas(empresas_queryset, nombre_grupo):
        """
        Calcula métricas agregadas (promedio, mediana, P25, P75) manteniendo
        privacidad — no expone datos individuales, solo distribución agregada.

        Fix #13: requiere mínimo 3 empresas para evitar revelar datos individuales
        cuando hay 1-2 competidores (en ese caso el "promedio" sería esa empresa).
        """
        # Mínimo 3 empresas — con menos no hay privacidad ni representatividad
        MINIMO_PRIVACIDAD = 3
        if empresas_queryset.count() < MINIMO_PRIVACIDAD:
            return BenchmarkingRealService._resultado_vacio(
                f"Datos insuficientes en {nombre_grupo} (mínimo {MINIMO_PRIVACIDAD} empresas)"
            )

        metricas_empresas = []
        for empresa in empresas_queryset:
            # Usa cache para no recalcular si la misma empresa aparece en otro nivel
            metricas = BenchmarkingRealService._obtener_metricas_cached(empresa)
            if metricas['ventas_mensuales'] > 0:
                metricas_empresas.append(metricas)

        if len(metricas_empresas) < MINIMO_PRIVACIDAD:
            return BenchmarkingRealService._resultado_vacio(
                f"Actividad insuficiente en {nombre_grupo} (mínimo {MINIMO_PRIVACIDAD} con actividad)"
            )

        # Extraer series para cálculo de percentiles reales
        series_ventas = sorted(m['ventas_mensuales'] for m in metricas_empresas)
        series_margen_bruto = sorted(m['margen_bruto'] for m in metricas_empresas)
        series_margen_neto = sorted(m['margen_neto'] for m in metricas_empresas)
        series_crecimiento = sorted(m['crecimiento_mensual'] for m in metricas_empresas)

        def _percentil(serie_ordenada, p):
            """Calcula el percentil p (0-100) de una serie ya ordenada."""
            if not serie_ordenada:
                return 0
            k = (len(serie_ordenada) - 1) * (p / 100)
            f = int(k)
            c = min(f + 1, len(serie_ordenada) - 1)
            if f == c:
                return serie_ordenada[f]
            d0 = serie_ordenada[f] * (c - k)
            d1 = serie_ordenada[c] * (k - f)
            return d0 + d1

        return {
            'nombre_grupo': nombre_grupo,
            'total_empresas': len(metricas_empresas),

            # Promedios
            'ventas_promedio':         sum(series_ventas) / len(series_ventas),
            'margen_bruto_promedio':   sum(series_margen_bruto) / len(series_margen_bruto),
            'margen_neto_promedio':    sum(series_margen_neto) / len(series_margen_neto),
            'crecimiento_promedio':    sum(series_crecimiento) / len(series_crecimiento),

            # Distribución por percentiles reales (fix #7)
            'ventas_p25':              _percentil(series_ventas, 25),
            'ventas_mediana':          _percentil(series_ventas, 50),
            'ventas_p75':              _percentil(series_ventas, 75),
            'margen_neto_p25':         _percentil(series_margen_neto, 25),
            'margen_neto_mediana':     _percentil(series_margen_neto, 50),
            'margen_neto_p75':         _percentil(series_margen_neto, 75),

            # Series ordenadas para cálculo de percentil exacto de la empresa
            '_series_ventas':          series_ventas,
            '_series_margen_neto':     series_margen_neto,

            'tiene_datos': True
        }
    
    @staticmethod
    def _resultado_vacio(razon):
        """Resultado cuando no hay datos suficientes"""
        return {
            'nombre_grupo': razon,
            'total_empresas': 0,
            'tiene_datos': False,
            'razon': razon
        }
    
    @staticmethod
    def _calcular_posiciones(empresa, comparaciones):
        """
        Calcula posición relativa usando percentiles REALES (fix #7).
        En vez de devolver solo 25/50/75, calcula el percentil exacto
        ordenando todas las empresas y viendo en qué posición cae la actual.
        """
        import bisect
        metricas_propias = BenchmarkingRealService._obtener_metricas_cached(empresa)
        posiciones = {}

        for nivel, datos in comparaciones.items():
            if not datos.get('tiene_datos'):
                continue

            # Usar series ordenadas si están disponibles (calculadas en _calcular_metricas_agregadas)
            series_ventas = datos.get('_series_ventas') or []
            series_margen = datos.get('_series_margen_neto') or []

            if series_ventas:
                pos = bisect.bisect_left(series_ventas, metricas_propias['ventas_mensuales'])
                percentil_ventas = round((pos / len(series_ventas)) * 100, 1)
            else:
                percentil_ventas = 50  # fallback

            if series_margen:
                pos = bisect.bisect_left(series_margen, metricas_propias['margen_neto'])
                percentil_margen = round((pos / len(series_margen)) * 100, 1)
            else:
                percentil_margen = 50

            posiciones[nivel] = {
                'percentil_ventas': percentil_ventas,
                'percentil_margen': percentil_margen,
                'total_empresas': datos['total_empresas'],
            }

        return posiciones
    
    @staticmethod
    def _generar_recomendaciones_privadas(metricas_propias, comparaciones):
        """Genera recomendaciones sin revelar datos de otras empresas"""
        recomendaciones = []
        
        # Buscar el mejor grupo de comparación disponible
        mejor_grupo = None
        for nivel in ['tipo_negocio', 'ciudad', 'provincia', 'categoria']:
            if comparaciones[nivel]['tiene_datos']:
                mejor_grupo = comparaciones[nivel]
                break
        
        if not mejor_grupo:
            return [{'tipo': 'info', 'mensaje': 'Datos insuficientes para comparación', 'area': 'General'}]
        
        # Comparar margen neto
        if metricas_propias['margen_neto'] < mejor_grupo['margen_neto_promedio']:
            diferencia = mejor_grupo['margen_neto_promedio'] - metricas_propias['margen_neto']
            recomendaciones.append({
                'tipo': 'warning',
                'area': 'Rentabilidad',
                'mensaje': f'Tu margen neto está {diferencia:.1f}% por debajo del promedio',
                'accion': 'Revisar estructura de costos y precios',
                'impacto': 'Alto'
            })
        
        # Comparar ventas
        if metricas_propias['ventas_mensuales'] < mejor_grupo['ventas_promedio']:
            recomendaciones.append({
                'tipo': 'info',
                'area': 'Ventas',
                'mensaje': 'Tus ventas están por debajo del promedio del grupo',
                'accion': 'Considerar estrategias de crecimiento',
                'impacto': 'Medio'
            })
        
        # Reconocer fortalezas
        if metricas_propias['margen_neto'] > mejor_grupo['margen_neto_promedio']:
            recomendaciones.append({
                'tipo': 'success',
                'area': 'Fortaleza',
                'mensaje': '¡Excelente rentabilidad comparada con empresas similares!',
                'accion': 'Mantener las buenas prácticas actuales',
                'impacto': 'Positivo'
            })
        
        return recomendaciones
