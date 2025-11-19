# empresa/views/resumen.py

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
    """Obtiene los totales contables estándar para toda la empresa"""
    try:
        cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
        ventas = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_ventas,
            tipo='credito'
        ).aggregate(total=Sum('monto'))['total'] or 0
    except CuentaContable.DoesNotExist:
        ventas = 0
    # Costos: Inventario (comercio) + Costo de Ventas (manufactura)
    compras = 0
    try:
        cuenta_inventario = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Inventario')
        compras += MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_inventario,
            tipo='debito'
        ).aggregate(total=Sum('monto'))['total'] or 0
    except CuentaContable.DoesNotExist:
        pass
    
    try:
        cuenta_costo_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Costo de Ventas')
        compras += MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_costo_ventas,
            tipo='debito'
        ).aggregate(total=Sum('monto'))['total'] or 0
    except CuentaContable.DoesNotExist:
        pass
    try:
        cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
        gastos = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_gastos,
            tipo='debito'
        ).aggregate(total=Sum('monto'))['total'] or 0
    except CuentaContable.DoesNotExist:
        gastos = 0
    utilidad_bruta = ventas - compras
    utilidad_neta = utilidad_bruta - gastos
    return {
        'ventas': float(ventas),
        'compras': float(compras),
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
    # Verificar empresa ANTES de todo
    empresa = getattr(request.user, 'empresa', None)
    if not empresa:
        from django.shortcuts import redirect
        from django.contrib import messages
        logger.warning(f"Usuario {request.user.username} sin empresa intentó acceder a resumen")
        messages.warning(request, 'Superusuario: usa /admin/ para gestión')
        return redirect('/admin/')
    
    try:
        # Datos por defecto
        totales = {
            'ventas': 0,
            'compras': 0, 
            'gastos': 0,
            'utilidad_bruta': 0,
            'utilidad_neta': 0
        }
        
        totales = obtener_totales_contables(empresa)
        productos_vendidos = obtener_productos_mas_vendidos(empresa)
        gastos_por_categoria = obtener_gastos_por_categoria(empresa)
    
        # 5. Generar recomendaciones automáticas
        recomendaciones = generar_recomendaciones(
            totales['ventas'],
            totales['gastos'],
            totales['utilidad_neta'],
            []
        )
        
        # 6. Generar conclusión ejecutiva
        conclusion = generar_conclusion_ejecutiva(
            totales['ventas'],
            totales['utilidad_neta']
        )
        
        # 7. Calcular indicadores financieros
        margen_neto = margen_bruto = ratio_gastos_ventas = ratio_costos = 0
        
        if empresa:
            try:
                margen_neto = (totales['utilidad_neta'] / totales['ventas'] * 100) if totales['ventas'] > 0 else 0
                margen_bruto = (totales['utilidad_bruta'] / totales['ventas'] * 100) if totales['ventas'] > 0 else 0
                ratio_gastos_ventas = (totales['gastos'] / totales['ventas'] * 100) if totales['ventas'] > 0 else 0
                ratio_costos = (totales['compras'] / totales['ventas'] * 100) if totales['ventas'] > 0 else 0
            except Exception as e:
                logger.error(f"Error calculando indicadores: {e}")

        # 8. Preparar contexto para el template
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
            'analisis_predictivo': {}
        }
        
        return render(request, 'empresa/resumen.html', contexto)
    
    except Exception as exc:
        # Log completo con traceback
        logger.exception("Error en vista resumen_financiero: %s", exc)
        # Respuesta controlada para el usuario
        from django.http import JsonResponse
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'error': 'Error al generar resumen financiero',
                'detail': str(exc) if request.user.is_superuser else 'Contacta soporte'
            }, status=500)
        
        try:
            return render(request, 'empresa/error_resumen.html', {
                "mensaje": "Error al generar el resumen financiero. El equipo técnico ha sido notificado."
            }, status=500)
        except:
            from django.http import HttpResponse
            return HttpResponse('Error 500: Resumen financiero no disponible', status=500)

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
    print(f"DEBUG - Estado de Resultados:")
    print(f"DEBUG - Ventas: {total_ventas}")
    print(f"DEBUG - Costos: {total_costos}")
    print(f"DEBUG - Gastos: {total_gastos}")
    print(f"DEBUG - Utilidad Operativa: {utilidad_operativa}")
    print(f"DEBUG - Utilidad Neta: {utilidad_neta}")

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
