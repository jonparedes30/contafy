# empresa/views/resumen.py

from empresa.utils.errores import mensaje_error
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from empresa.models import Venta, Compra, Gasto, CuentaContable, MovimientoContable, Producto
from django.db.models import Sum
from datetime import datetime, timedelta
import calendar
import json
import logging

logger = logging.getLogger(__name__)


def obtener_totales_contables(empresa):
    """Totales del estado de resultados de toda la empresa, desde el libro contable.

    Utilidad bruta = Ventas - Costo de Ventas (costo de la mercadería vendida).
    Las compras NO se restan: comprar mercadería aumenta el Inventario (un
    activo) y solo se vuelve costo cuando esa mercadería se vende.

    La clave 'compras' se conserva por compatibilidad y vale lo mismo que
    'costo_ventas'.
    """
    from empresa.services.saldos import saldo_cuenta

    ventas = saldo_cuenta(empresa, 'Ventas')
    costo_ventas = saldo_cuenta(empresa, 'Costo de Ventas')
    gastos = saldo_cuenta(empresa, 'Gastos')
    utilidad_bruta = ventas - costo_ventas
    utilidad_neta = utilidad_bruta - gastos
    return {
        'ventas': float(ventas),
        'costo_ventas': float(costo_ventas),
        'compras': float(costo_ventas),
        'gastos': float(gastos),
        'utilidad_bruta': float(utilidad_bruta),
        'utilidad_neta': float(utilidad_neta)
    }


def obtener_datos_grafico_tendencia(empresa, cuenta_ventas, cuenta_gastos):
    """Obtiene datos para el gráfico de tendencia de los últimos 12 meses"""
    
    datos_grafico = []
    
    for i in range(11, -1, -1):
        fecha = datetime.now().replace(day=1) - timedelta(days=30*i)
        mes = fecha.month
        año = fecha.year
        
        # Ventas del mes
        ventas_mes = 0
        if cuenta_ventas:
            try:
                ventas_mes = MovimientoContable.objects.filter(
                    empresa=empresa,
                    cuenta_fk=cuenta_ventas,
                    tipo='credito',
                    fecha__month=mes,
                    fecha__year=año
                ).aggregate(total=Sum('monto'))['total'] or 0
            except:
                pass
        
        # Gastos del mes
        gastos_mes = 0
        if cuenta_gastos:
            try:
                gastos_mes = MovimientoContable.objects.filter(
                    empresa=empresa,
                    cuenta_fk=cuenta_gastos,
                    tipo='debito',
                    fecha__month=mes,
                    fecha__year=año
                ).aggregate(total=Sum('monto'))['total'] or 0
            except:
                pass
        
        datos_grafico.append({
            'mes': fecha.strftime('%b %Y'),
            'ventas': float(ventas_mes),
            'gastos': float(gastos_mes)
        })
    
    return datos_grafico


def obtener_productos_mas_vendidos(empresa):
    """Obtiene los productos más vendidos"""
    productos_vendidos = Venta.objects.filter(empresa=empresa).values(
        'producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum('monto')
    ).order_by('-total_ingresos')[:5]
    
    return list(productos_vendidos)


def obtener_gastos_por_categoria(empresa):
    """Obtiene los gastos agrupados por categoría"""
    gastos_por_categoria = Gasto.objects.filter(empresa=empresa).values(
        'categoria'
    ).annotate(
        total=Sum('monto')
    ).order_by('-total')
    
    return list(gastos_por_categoria)


def generar_recomendaciones(ventas, gastos, utilidad_neta, datos_grafico):
    """Genera recomendaciones automáticas basadas en los datos financieros"""
    
    recomendaciones = []
    
    # Análisis de utilidad
    if ventas > 0:
        margen_utilidad = (utilidad_neta / ventas) * 100
        
        if margen_utilidad < 5:
            recomendaciones.append({
                'tipo': 'danger',
                'titulo': 'Margen de utilidad crítico',
                'descripcion': f'Tu margen de utilidad es del {margen_utilidad:.1f}%. Urgente: revisa precios y reduce costos operativos.'
            })
        elif margen_utilidad < 15:
            recomendaciones.append({
                'tipo': 'warning',
                'titulo': 'Margen de utilidad bajo',
                'descripcion': f'Tu margen de utilidad es del {margen_utilidad:.1f}%. Considera optimizar precios o reducir costos.'
            })
        elif margen_utilidad > 25:
            recomendaciones.append({
                'tipo': 'success',
                'titulo': 'Excelente rentabilidad',
                'descripcion': f'Tu margen de utilidad del {margen_utilidad:.1f}% es muy saludable. Considera reinvertir en crecimiento.'
            })
    
    # Análisis de gastos vs ventas
    if ventas > 0:
        ratio_gastos = (gastos / ventas) * 100
        
        if ratio_gastos > 70:
            recomendaciones.append({
                'tipo': 'danger',
                'titulo': 'Gastos excesivos',
                'descripcion': f'Los gastos representan el {ratio_gastos:.1f}% de tus ventas. Implementa un plan de reducción de costos.'
            })
        elif ratio_gastos > 50:
            recomendaciones.append({
                'tipo': 'warning',
                'titulo': 'Gastos elevados',
                'descripcion': f'Los gastos representan el {ratio_gastos:.1f}% de tus ventas. Revisa gastos no esenciales.'
            })
    
    # Análisis de flujo de caja
    if utilidad_neta < 0:
        recomendaciones.append({
            'tipo': 'danger',
            'titulo': 'Pérdidas operativas',
            'descripcion': f'Tu empresa tiene pérdidas de ${abs(utilidad_neta):,.2f}. Prioriza generar ingresos y controlar gastos.'
        })
    elif utilidad_neta > 0 and utilidad_neta < ventas * 0.05:
        recomendaciones.append({
            'tipo': 'warning',
            'titulo': 'Utilidad marginal',
            'descripcion': f'Tus utilidades son bajas (${utilidad_neta:,.2f}). Busca oportunidades de mejora en eficiencia.'
        })
    
    # Análisis de escala de negocio
    if ventas > 0 and ventas < 10000:
        recomendaciones.append({
            'tipo': 'info',
            'titulo': 'Oportunidad de crecimiento',
            'descripcion': 'Tu negocio tiene potencial de expansión. Considera estrategias de marketing y nuevos productos.'
        })
    elif ventas > 50000:
        recomendaciones.append({
            'tipo': 'success',
            'titulo': 'Negocio consolidado',
            'descripcion': 'Tu empresa muestra un volumen sólido. Evalúa oportunidades de diversificación o expansión.'
        })
    
    # Recomendación de control financiero
    if len(recomendaciones) == 0:
        recomendaciones.append({
            'tipo': 'success',
            'titulo': 'Buen control financiero',
            'descripcion': 'Tus indicadores financieros están en rangos saludables. Mantén el monitoreo constante.'
        })
    
    return recomendaciones


def generar_conclusion_ejecutiva(ventas, utilidad_neta):
    """Genera la conclusión ejecutiva basada en el estado financiero"""
    
    if utilidad_neta > 0:
        if utilidad_neta > ventas * 0.2:
            return {
                'estado': 'excelente',
                'titulo': 'Estado financiero excelente',
                'descripcion': 'Tu empresa muestra un rendimiento financiero sobresaliente con utilidades sólidas y tendencias positivas.'
            }
        else:
            return {
                'estado': 'bueno',
                'titulo': 'Estado financiero estable',
                'descripcion': 'Tu empresa mantiene un estado financiero estable. Hay oportunidades de mejora identificadas.'
            }
    else:
        return {
            'estado': 'atencion',
            'titulo': 'Atención requerida',
            'descripcion': 'Tu empresa presenta pérdidas. Es importante revisar la estrategia de costos y precios.'
        }


@login_required
def resumen_financiero(request):
    """Vista principal del resumen financiero"""
    from django.http import HttpResponse
    
    # Log inicial
    logger.info(f"=== RESUMEN: Usuario {request.user.username} ====")
    
    # Verificar empresa
    empresa = getattr(request.user, 'empresa', None)
    logger.info(f"Empresa: {empresa}")
    
    if not empresa:
        from django.shortcuts import redirect
        from django.contrib import messages
        logger.warning(f"Usuario sin empresa")
        messages.warning(request, 'Superusuario: usa /admin/ para gestión')
        return redirect('/admin/')
    
    try:
        logger.info("Obteniendo totales contables...")
        totales = obtener_totales_contables(empresa)
        logger.info(f"Totales OK: {totales}")
        
        logger.info("Obteniendo productos vendidos...")
        productos_vendidos = obtener_productos_mas_vendidos(empresa)
        logger.info(f"Productos OK: {len(productos_vendidos)}")
        
        logger.info("Obteniendo gastos por categoría...")
        gastos_por_categoria = obtener_gastos_por_categoria(empresa)
        logger.info(f"Gastos OK: {len(gastos_por_categoria)}")
        
        logger.info("Generando recomendaciones...")
        recomendaciones = generar_recomendaciones(
            totales['ventas'],
            totales['gastos'],
            totales['utilidad_neta'],
            []
        )
        logger.info(f"Recomendaciones OK: {len(recomendaciones)}")
        
        logger.info("Generando conclusión...")
        conclusion = generar_conclusion_ejecutiva(
            totales['ventas'],
            totales['utilidad_neta']
        )
        logger.info(f"Conclusión OK")
        
        logger.info("Calculando indicadores...")
        margen_neto = (totales['utilidad_neta'] / totales['ventas'] * 100) if totales['ventas'] > 0 else 0
        margen_bruto = (totales['utilidad_bruta'] / totales['ventas'] * 100) if totales['ventas'] > 0 else 0
        ratio_gastos_ventas = (totales['gastos'] / totales['ventas'] * 100) if totales['ventas'] > 0 else 0
        ratio_costos = (totales['compras'] / totales['ventas'] * 100) if totales['ventas'] > 0 else 0
        
        # Indicadores de solvencia con saldos reales del libro contable.
        from empresa.services.saldos import resumen_balance
        balance = resumen_balance(empresa)
        activo_corriente = float(balance['activo_corriente'])
        total_activos_f = float(balance['activo_total'])
        total_pasivos_f = float(balance['pasivo_total'])
        # Patrimonio = capital aportado + resultado del ejercicio (aún no cerrado a capital).
        patrimonio = float(balance['capital']) + totales['utilidad_neta']
        ventas_f = float(totales['ventas'])

        # Liquidez corriente: activo corriente / pasivo (todo el pasivo actual es de corto plazo).
        liquidez = round(activo_corriente / total_pasivos_f, 2) if total_pasivos_f > 0 else None
        endeudamiento = round(total_pasivos_f / total_activos_f, 2) if total_activos_f > 0 else 0.0
        rotacion_activos = round(ventas_f / total_activos_f, 2) if total_activos_f > 0 else 0.0
        roe = round(totales['utilidad_neta'] / patrimonio * 100, 2) if patrimonio > 0 else None
        
        logger.info(f"Indicadores de solvencia OK: liquidez={liquidez}, endeudamiento={endeudamiento}, rotacion={rotacion_activos}")
        
        logger.info("Generando análisis predictivo...")
        
        # Determinar tendencia basada en datos actuales
        utilidad_neta = totales.get('utilidad_neta', 0)
        utilidad_bruta = totales.get('utilidad_bruta', 0)
        ventas = totales.get('ventas', 0)
        
        # Tendencia: positiva si hay utilidad neta positiva
        tendencia_nivel = 'Positiva' if utilidad_neta > 0 else 'Negativa' if utilidad_neta < 0 else 'Estable'
        tendencia_color = 'positivo' if utilidad_neta > 0 else 'negativo' if utilidad_neta < 0 else 'neutro'
        
        # Riesgo de quiebra: basado en el margen neto
        margen_neto_calc = (utilidad_neta / ventas * 100) if ventas > 0 else 0
        if margen_neto_calc > 15:
            riesgo_nivel = 'Bajo'
        elif margen_neto_calc > 5:
            riesgo_nivel = 'Medio'
        else:
            riesgo_nivel = 'Alto'
        
        # Probabilidad de crecimiento: basada en tendencia positiva
        probabilidad_crecimiento = 70 if utilidad_neta > 0 and ventas > 0 else 30
        
        # Z-Score de Altman simplificado
        z_score = 2.5 if utilidad_neta > 0 else 1.5 if margen_neto_calc > 0 else 0.9
        
        analisis_predictivo = {
            'tendencia_general': {'nivel': tendencia_nivel, 'color': tendencia_color},
            'riesgo_quiebra': {'nivel': riesgo_nivel},
            'probabilidad_crecimiento': probabilidad_crecimiento,
            'z_score': z_score,
            'alertas_tempranas': []
        }
        
        # Intentar obtener análisis más avanzado si el servicio está disponible
        try:
            from empresa.services.predicciones_service import PrediccionesAvanzadas
            predicciones_service = PrediccionesAvanzadas(empresa)
            
            flujo_caja = predicciones_service.predecir_flujo_caja(meses=6)
            logger.info(f"Flujo caja avanzado disponible: {flujo_caja.get('success')}")
            
            if flujo_caja.get('success'):
                # Usar datos avanzados si están disponibles
                analisis_predictivo['predicciones'] = flujo_caja.get('predicciones', [])
                analisis_predictivo['confianza'] = flujo_caja.get('confianza', 'Media')
            
            riesgo_quiebra = predicciones_service.detectar_riesgo_quiebra()
            logger.info(f"Riesgo quiebra avanzado disponible: {riesgo_quiebra.get('success')}")
            
            if riesgo_quiebra.get('success'):
                # Actualizar con datos avanzados
                alertas = []
                for key, ind in riesgo_quiebra.get('indicadores', {}).items():
                    if ind.get('riesgo') == 'Alto':
                        alertas.append({
                            'tipo': 'critico',
                            'prioridad': 'Alta',
                            'mensaje': f"{ind.get('descripcion', key)}: {ind.get('valor', 'N/A')}"
                        })
                if alertas:
                    analisis_predictivo['alertas_tempranas'] = alertas
            
        except Exception as e:
            logger.info(f"Análisis predictivo avanzado no disponible: {e}. Usando análisis básico.")
        
        logger.info(f"Análisis predictivo OK: {analisis_predictivo}")
        
        logger.info(f"Análisis predictivo OK: {analisis_predictivo}")
        
        logger.info("Preparando contexto...")
        contexto = {
            'ventas': totales.get('ventas', 0),
            'compras': totales.get('compras', 0),
            'gastos': totales.get('gastos', 0),
            'utilidad_bruta': totales.get('utilidad_bruta', 0),
            'utilidad_neta': totales.get('utilidad_neta', 0),
            'productos_vendidos': productos_vendidos,
            'gastos_por_categoria': gastos_por_categoria,
            'recomendaciones': recomendaciones,
            'conclusion': conclusion,
            'margen_neto': round(float(margen_neto), 2),
            'margen_bruto': round(float(margen_bruto), 2),
            'ratio_gastos_ventas': round(float(ratio_gastos_ventas), 2),
            'ratio_costos': round(float(ratio_costos), 2),
            # Indicadores de solvencia
            'liquidez': liquidez,
            'endeudamiento': endeudamiento,
            'rotacion_activos': rotacion_activos,
            'roe': roe,
            'costo_ventas': totales.get('costo_ventas', 0),
            'total_activos': round(total_activos_f, 2),
            'total_pasivos': round(total_pasivos_f, 2),
            'total_capital': round(patrimonio, 2),
            'analisis_predictivo': analisis_predictivo
        }
        logger.info("Contexto OK")

        # Normalizar contexto usando Presenter según categoría
        try:
            from empresa.presenters.resumen_presenter import ResumenPresenter
            from empresa.presenters.comercio_presenter import ComercioPresenter
            from empresa.presenters.servicio_presenter import ServicioPresenter
            
            categoria = getattr(empresa, 'categoria', 'default') or 'default'
            
            # Usar presenter específico según categoría
            if categoria == 'comercio':
                presenter = ComercioPresenter(empresa=empresa)
                contexto.update(presenter.to_context())
            elif categoria == 'servicio':
                presenter = ServicioPresenter(empresa=empresa)
                contexto.update(presenter.to_context())
            else:
                # Default: usar ResumenPresenter para manufactura u otros
                presenter = ResumenPresenter(empresa=empresa, data=contexto)
                contexto = presenter.to_context()
        except Exception as e:
            logger.exception(f"Error inicializando presenter: {e}")

        # Asegurar que los indicadores de solvencia siempre están en el contexto
        contexto['liquidez'] = liquidez
        contexto['endeudamiento'] = endeudamiento
        contexto['rotacion_activos'] = rotacion_activos
        contexto['roe'] = roe
        contexto['total_activos'] = round(total_activos_f, 2)
        contexto['total_pasivos'] = round(total_pasivos_f, 2)
        contexto['total_capital'] = round(patrimonio, 2)
        contexto['analisis_predictivo'] = analisis_predictivo

        logger.info("Renderizando template...")
        # Selección de plantilla por categoría con fallback
        prefix = getattr(empresa, 'categoria', 'default') or 'default'
        templates = [f'empresa/{prefix}/resumen.html', 'empresa/resumen.html']
        return render(request, templates, contexto)
    
    except Exception as exc:
        logger.exception(f"ERROR CRÍTICO en resumen: {exc}")
        return HttpResponse(f'Error 500: {mensaje_error(exc)}', status=500)

@login_required
def estado_resultados(request):
    empresa = getattr(request.user, 'empresa', None)
    if not empresa:
        return render(request, 'empresa/error_resumen.html', {
            "mensaje": "No tienes una empresa asociada. Por favor contacta al administrador."
        }, status=400)
    
    # Obtener filtros de fecha
    from empresa.services.filtros_service import FiltrosFechaService
    fecha_inicio, fecha_fin = FiltrosFechaService.obtener_rango_fechas(request)

    # Ventas: suma de movimientos contables en cuenta 'Ventas' (crédito) con filtro de fecha
    try:
        cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
        total_ventas = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_ventas,
            tipo='credito',
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).aggregate(total=Sum('monto'))['total'] or 0
    except CuentaContable.DoesNotExist:
        total_ventas = 0

    # Costos: suma de movimientos contables en cuenta 'Inventario' (débito) con filtro de fecha
    try:
        cuenta_inventario = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Inventario')
        total_costos = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_inventario,
            tipo='debito',
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).aggregate(total=Sum('monto'))['total'] or 0
    except CuentaContable.DoesNotExist:
        total_costos = 0

    # Gastos: suma de movimientos contables en cuenta 'Gastos' (débito) con filtro de fecha
    try:
        cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
        total_gastos = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_gastos,
            tipo='debito',
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).aggregate(total=Sum('monto'))['total'] or 0
    except CuentaContable.DoesNotExist:
        total_gastos = 0

    utilidad_operativa = total_ventas - total_costos
    utilidad_neta = utilidad_operativa - total_gastos

    # Debug: Imprimir valores calculados
    logger.debug(f"DEBUG - Estado de Resultados:")
    logger.debug(f"DEBUG - Ventas: {total_ventas}")
    logger.debug(f"DEBUG - Costos: {total_costos}")
    logger.debug(f"DEBUG - Gastos: {total_gastos}")
    logger.debug(f"DEBUG - Utilidad Operativa: {utilidad_operativa}")
    logger.debug(f"DEBUG - Utilidad Neta: {utilidad_neta}")

    contexto = {
        'ventas': float(total_ventas or 0.0),
        'costos': float(total_costos or 0.0),
        'gastos': float(total_gastos or 0.0),
        'utilidad_operativa': float(utilidad_operativa or 0.0),
        'utilidad_neta': float(utilidad_neta or 0.0),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'empresa/estado_resultado.html', contexto)
