from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg
from django.http import JsonResponse
from datetime import datetime, timedelta
from empresa.models import MetaFinanciera, Venta, Gasto, HistorialMeta, NotificacionMeta
from empresa.services.metas_service import ServicioMetas
import json

@login_required
def gestionar_metas(request):
    empresa = request.user.empresa

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        objetivo_mensual = request.POST.get('objetivo_mensual')
        mes = request.POST.get('mes')
        anio = request.POST.get('anio')
        es_dinamica = request.POST.get('es_dinamica') == 'on'
        factor_ajuste = request.POST.get('factor_ajuste', 1.0)
        recordatorio_dias = request.POST.get('recordatorio_dias', 7)
        alertas_activas = request.POST.get('alertas_activas') == 'on'

        if tipo and objetivo_mensual and mes and anio:
            try:
                # Verificar si ya existe una meta para este tipo, mes y año
                meta_existente = MetaFinanciera.objects.filter(
                    empresa=empresa,
                    tipo=tipo,
                    mes=int(mes),
                    anio=int(anio)
                ).first()
                
                if meta_existente:
                    # Actualizar meta existente
                    meta_existente.objetivo_mensual = float(objetivo_mensual)
                    meta_existente.es_dinamica = es_dinamica
                    meta_existente.factor_ajuste = float(factor_ajuste)
                    meta_existente.recordatorio_dias = int(recordatorio_dias)
                    meta_existente.alertas_activas = alertas_activas
                    meta_existente.save()
                    messages.success(request, 'Meta actualizada exitosamente.')
                else:
                    # Crear nueva meta
                    MetaFinanciera.objects.create(
                        empresa=empresa,
                        tipo=tipo,
                        objetivo_mensual=float(objetivo_mensual),
                        mes=int(mes),
                        anio=int(anio),
                        es_dinamica=es_dinamica,
                        factor_ajuste=float(factor_ajuste),
                        recordatorio_dias=int(recordatorio_dias),
                        alertas_activas=alertas_activas
                    )
                    messages.success(request, 'Meta creada exitosamente.')
                
                return redirect('empresa:gestionar_metas')
            except Exception as e:
                messages.error(request, f'Error al guardar la meta: {str(e)}')

    # Obtener metas existentes y pre-calcular propiedades para evitar N+1 queries
    metas_qs = MetaFinanciera.objects.filter(empresa=empresa).order_by('-anio', '-mes')
    metas = []
    for meta in metas_qs:
        # Cachear valores calculados para evitar queries repetidas en el template
        meta._cached_valor_actual = meta.valor_actual
        meta._cached_progreso_actual = meta.progreso_actual
        meta._cached_estado = meta.estado
        metas.append(meta)
    
    # Calcular estadísticas de benchmarking
    estadisticas = calcular_benchmarking(empresa)
    
    # Obtener recomendaciones
    recomendaciones = ServicioMetas.generar_recomendaciones_metas(empresa)
    
    # Obtener benchmarking sectorial con datos reales
    benchmarking_sectorial = ServicioMetas.calcular_benchmarking_sectorial(empresa)
    
    # Extraer análisis predictivo para dashboard
    analisis_predictivo = benchmarking_sectorial.get('analisis_predictivo', {})
    
    # Obtener sugerencias de metas dinámicas
    metas_dinamicas = ServicioMetas.generar_metas_dinamicas(empresa)
    
    # Obtener notificaciones pendientes
    notificaciones = ServicioMetas.obtener_notificaciones_pendientes(empresa)
    
    # Datos históricos mensuales para gráficos (últimos 6 meses)
    datos_historicos = _obtener_datos_historicos_mensuales(empresa)
    
    # Nombres de meses en español
    MESES_ES = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    historico_labels = json.dumps([
        f"{MESES_ES[d['mes']]} {d['anio']}" for d in datos_historicos
    ])
    historico_ventas = json.dumps([float(d['ventas']) for d in datos_historicos])
    historico_gastos = json.dumps([float(d['gastos']) for d in datos_historicos])
    historico_rentabilidad = json.dumps([float(d['rentabilidad']) for d in datos_historicos])
    tiene_datos_historicos = any(d['ventas'] > 0 or d['gastos'] > 0 for d in datos_historicos)
    
    # Lista de meses en español
    meses_es = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    return render(request, 'empresa/metas.html', {
        'metas': metas,
        'estadisticas': estadisticas,
        'recomendaciones': recomendaciones,
        'benchmarking_sectorial': benchmarking_sectorial,
        'analisis_predictivo': analisis_predictivo,
        'metas_dinamicas': metas_dinamicas,
        'notificaciones': notificaciones,
        'tipos_meta': MetaFinanciera._meta.get_field('tipo').choices,
        'meses': meses_es,
        'anios': range(2020, datetime.now().year + 2),
        'historico_labels': historico_labels,
        'historico_ventas': historico_ventas,
        'historico_gastos': historico_gastos,
        'historico_rentabilidad': historico_rentabilidad,
        'tiene_datos_historicos': tiene_datos_historicos,
    })

@login_required
def historial_meta(request, meta_id):
    """Vista para mostrar el historial de una meta específica"""
    meta = get_object_or_404(MetaFinanciera, id=meta_id, empresa=request.user.empresa)
    historial = HistorialMeta.objects.filter(meta=meta).order_by('-fecha_registro')
    
    return render(request, 'empresa/historial_meta.html', {
        'meta': meta,
        'historial': historial
    })

@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """API para marcar una notificación como leída"""
    if request.method == 'POST':
        success = ServicioMetas.marcar_notificacion_leida(notificacion_id)
        return JsonResponse({'success': success})
    return JsonResponse({'success': False})

@login_required
def comparacion_sector(request):
    empresa = request.user.empresa
    
    # Obtener benchmarking sectorial con datos reales
    benchmarking_sectorial = ServicioMetas.calcular_benchmarking_sectorial(empresa)
    
    # Datos históricos mensuales para gráficos (últimos 6 meses)
    datos_historicos = _obtener_datos_historicos_mensuales(empresa)
    
    # Nombres de meses en español
    MESES_ES = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    historico_labels = json.dumps([
        f"{MESES_ES[d['mes']]} {d['anio']}" for d in datos_historicos
    ])
    historico_ventas = json.dumps([float(d['ventas']) for d in datos_historicos])
    historico_gastos = json.dumps([float(d['gastos']) for d in datos_historicos])
    historico_rentabilidad = json.dumps([float(d['rentabilidad']) for d in datos_historicos])
    tiene_datos_historicos = any(d['ventas'] > 0 or d['gastos'] > 0 for d in datos_historicos)
    
    context = {
        'benchmarking_sectorial': benchmarking_sectorial,
        'historico_labels': historico_labels,
        'historico_ventas': historico_ventas,
        'historico_gastos': historico_gastos,
        'historico_rentabilidad': historico_rentabilidad,
        'tiene_datos_historicos': tiene_datos_historicos,
    }
    return render(request, 'empresa/comparacion_sector.html', context)

def _obtener_datos_historicos_mensuales(empresa, meses=6):
    """Obtiene datos mensuales de ventas, gastos y rentabilidad para los últimos N meses."""
    datos = []
    hoy = datetime.now()
    
    for i in range(meses - 1, -1, -1):  # Orden cronológico (más antiguo primero)
        # Cálculo exacto de mes/año retrocediendo i meses
        mes = hoy.month - i
        anio = hoy.year
        while mes <= 0:
            mes += 12
            anio -= 1
        
        ventas_mes = Venta.objects.filter(
            empresa=empresa,
            fecha__month=mes,
            fecha__year=anio
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        gastos_mes = Gasto.objects.filter(
            empresa=empresa,
            fecha__month=mes,
            fecha__year=anio
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        utilidad = float(ventas_mes) - float(gastos_mes)
        rentabilidad = (utilidad / float(ventas_mes) * 100) if float(ventas_mes) > 0 else 0
        
        datos.append({
            'mes': mes,
            'anio': anio,
            'ventas': ventas_mes,
            'gastos': gastos_mes,
            'utilidad': utilidad,
            'rentabilidad': round(rentabilidad, 1),
        })
    
    return datos


def calcular_benchmarking(empresa):
    """Calcula estadísticas de benchmarking para la empresa"""
    from django.db.models import Avg, Count
    
    # Estadísticas de ventas
    ventas_mensuales = Venta.objects.filter(empresa=empresa).aggregate(
        promedio_mensual=Avg('monto'),
        total_ventas=Sum('monto'),
        cantidad_ventas=Count('id')
    )
    
    # Estadísticas de gastos
    gastos_mensuales = Gasto.objects.filter(empresa=empresa).aggregate(
        promedio_mensual=Avg('monto'),
        total_gastos=Sum('monto'),
        cantidad_gastos=Count('id')
    )
    
    # Calcular utilidad
    utilidad_total = (ventas_mensuales['total_ventas'] or 0) - (gastos_mensuales['total_gastos'] or 0)
    
    # Margen de utilidad
    margen_utilidad = 0
    if ventas_mensuales['total_ventas'] and ventas_mensuales['total_ventas'] > 0:
        margen_utilidad = (utilidad_total / ventas_mensuales['total_ventas']) * 100
    
    return {
        'ventas_promedio_mensual': ventas_mensuales['promedio_mensual'] or 0,
        'gastos_promedio_mensual': gastos_mensuales['promedio_mensual'] or 0,
        'utilidad_total': utilidad_total,
        'margen_utilidad': margen_utilidad,
        'total_ventas': ventas_mensuales['total_ventas'] or 0,
        'total_gastos': gastos_mensuales['total_gastos'] or 0,
        'cantidad_ventas': ventas_mensuales['cantidad_ventas'] or 0,
        'cantidad_gastos': gastos_mensuales['cantidad_gastos'] or 0,
    }
