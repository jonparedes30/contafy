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
    
    @staticmethod
    def obtener_benchmarking_completo(empresa):
        """Obtiene benchmarking completo con datos reales por niveles geográficos"""
        
        # Calcular métricas propias
        metricas_propias = BenchmarkingRealService._calcular_metricas_empresa(empresa)
        
        # Obtener comparaciones por niveles
        comparaciones = {
            'categoria': BenchmarkingRealService._benchmarking_por_categoria(empresa),
            'tipo_negocio': BenchmarkingRealService._benchmarking_por_tipo_negocio(empresa),
            'ciudad': BenchmarkingRealService._benchmarking_por_ciudad(empresa),
            'provincia': BenchmarkingRealService._benchmarking_por_provincia(empresa),
            'pais': BenchmarkingRealService._benchmarking_nacional(empresa),
            'cercanas_100km': BenchmarkingRealService._benchmarking_100km(empresa)
        }
        
        # Calcular percentiles y posiciones
        posiciones = BenchmarkingRealService._calcular_posiciones(empresa, comparaciones)
        
        # Generar recomendaciones
        recomendaciones = BenchmarkingRealService._generar_recomendaciones_privadas(
            metricas_propias, comparaciones
        )
        
        return {
            'metricas_propias': metricas_propias,
            'comparaciones': comparaciones,
            'posiciones': posiciones,
            'recomendaciones': recomendaciones
        }
    
    @staticmethod
    def _calcular_metricas_empresa(empresa):
        """Calcula métricas de la empresa usando datos contables reales"""
        hoy = timezone.now()
        inicio_mes = hoy.replace(day=1)
        hace_3_meses = hoy - timedelta(days=90)
        hace_6_meses = hoy - timedelta(days=180)
        
        # Ventas mensuales (desde movimientos contables)
        try:
            cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
            ventas_mes = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                fecha__gte=inicio_mes
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            ventas_3m = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                fecha__gte=hace_3_meses
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            ventas_6m = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                fecha__gte=hace_6_meses
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            ventas_mes = ventas_3m = ventas_6m = 0
        
        # Gastos mensuales
        try:
            cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
            gastos_mes = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_gastos, tipo='debito',
                fecha__gte=inicio_mes
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            gastos_mes = 0
        
        # Costos (Inventario/Compras)
        try:
            cuentas_inventario = CuentaContable.objects.filter(
                empresa=empresa, 
                nombre__in=['Inventario', 'Inventario de Materias Primas', 'Costo de Ventas']
            )
            costos_mes = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk__in=cuentas_inventario, tipo='debito',
                fecha__gte=inicio_mes
            ).aggregate(total=Sum('monto'))['total'] or 0
        except:
            costos_mes = 0
        
        # Calcular métricas
        utilidad_bruta = ventas_mes - costos_mes
        utilidad_neta = utilidad_bruta - gastos_mes
        
        margen_bruto = (utilidad_bruta / ventas_mes * 100) if ventas_mes > 0 else 0
        margen_neto = (utilidad_neta / ventas_mes * 100) if ventas_mes > 0 else 0
        
        # Crecimiento
        ventas_mes_anterior = (ventas_3m - ventas_mes) / 2 if ventas_3m > ventas_mes else 0
        crecimiento_mensual = ((ventas_mes - ventas_mes_anterior) / ventas_mes_anterior * 100) if ventas_mes_anterior > 0 else 0
        
        return {
            'ventas_mensuales': float(ventas_mes),
            'gastos_mensuales': float(gastos_mes),
            'costos_mensuales': float(costos_mes),
            'utilidad_bruta': float(utilidad_bruta),
            'utilidad_neta': float(utilidad_neta),
            'margen_bruto': float(margen_bruto),
            'margen_neto': float(margen_neto),
            'crecimiento_mensual': float(crecimiento_mensual),
            'ventas_trimestre': float(ventas_3m),
            'ventas_semestre': float(ventas_6m)
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
        empresas_pais = Empresa.objects.filter(
            categoria=empresa.categoria
        ).exclude(id=empresa.id)
        
        return BenchmarkingRealService._calcular_metricas_agregadas(
            empresas_pais, "Nacional"
        )
    
    @staticmethod
    def _benchmarking_100km(empresa):
        """Benchmarking de empresas en 100km a la redonda"""
        if not (empresa.latitud and empresa.longitud):
            return BenchmarkingRealService._resultado_vacio("Coordenadas GPS no disponibles")
        
        empresas_con_gps = Empresa.objects.filter(
            latitud__isnull=False,
            longitud__isnull=False
        ).exclude(id=empresa.id)
        
        empresas_cercanas_ids = []
        for emp in empresas_con_gps:
            distancia = calcular_distancia_km(
                float(empresa.latitud), float(empresa.longitud),
                float(emp.latitud), float(emp.longitud)
            )
            if distancia and distancia <= 100:
                empresas_cercanas_ids.append(emp.id)
        
        empresas_cercanas = Empresa.objects.filter(id__in=empresas_cercanas_ids)
        
        return BenchmarkingRealService._calcular_metricas_agregadas(
            empresas_cercanas, "100km a la redonda"
        )
    
    @staticmethod
    def _calcular_metricas_agregadas(empresas_queryset, nombre_grupo):
        """Calcula métricas agregadas manteniendo privacidad"""
        minimo_empresas = 2 if 'Ciudad' in nombre_grupo or '100km' in nombre_grupo else 3
        if empresas_queryset.count() < minimo_empresas:
            return BenchmarkingRealService._resultado_vacio(f"Datos insuficientes en {nombre_grupo}")
        
        hoy = timezone.now()
        inicio_mes = hoy.replace(day=1)
        
        metricas_empresas = []
        
        for empresa in empresas_queryset:
            metricas = BenchmarkingRealService._calcular_metricas_empresa(empresa)
            if metricas['ventas_mensuales'] > 0:  # Solo empresas con actividad
                metricas_empresas.append(metricas)
        
        minimo_actividad = 2 if 'Ciudad' in nombre_grupo or '100km' in nombre_grupo else 3
        if len(metricas_empresas) < minimo_actividad:
            return BenchmarkingRealService._resultado_vacio(f"Actividad insuficiente en {nombre_grupo}")
        
        # Calcular promedios (mantiene privacidad)
        return {
            'nombre_grupo': nombre_grupo,
            'total_empresas': len(metricas_empresas),
            'ventas_promedio': sum(m['ventas_mensuales'] for m in metricas_empresas) / len(metricas_empresas),
            'margen_bruto_promedio': sum(m['margen_bruto'] for m in metricas_empresas) / len(metricas_empresas),
            'margen_neto_promedio': sum(m['margen_neto'] for m in metricas_empresas) / len(metricas_empresas),
            'crecimiento_promedio': sum(m['crecimiento_mensual'] for m in metricas_empresas) / len(metricas_empresas),
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
        """Calcula posición relativa sin revelar datos individuales"""
        metricas_propias = BenchmarkingRealService._calcular_metricas_empresa(empresa)
        posiciones = {}
        
        for nivel, datos in comparaciones.items():
            if datos['tiene_datos']:
                # Calcular percentil aproximado (sin revelar datos exactos)
                pos_ventas = 50  # Default
                pos_margen = 50
                
                if metricas_propias['ventas_mensuales'] > datos['ventas_promedio']:
                    pos_ventas = 75  # Por encima del promedio
                elif metricas_propias['ventas_mensuales'] < datos['ventas_promedio'] * 0.8:
                    pos_ventas = 25  # Significativamente por debajo
                
                if metricas_propias['margen_neto'] > datos['margen_neto_promedio']:
                    pos_margen = 75
                elif metricas_propias['margen_neto'] < datos['margen_neto_promedio'] * 0.8:
                    pos_margen = 25
                
                posiciones[nivel] = {
                    'percentil_ventas': pos_ventas,
                    'percentil_margen': pos_margen,
                    'total_empresas': datos['total_empresas']
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