from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg
from django.http import JsonResponse
from datetime import datetime, timedelta
from empresa.models import MetaFinanciera, Venta, Gasto, HistorialMeta, NotificacionMeta
from empresa.services.metas_service import ServicioMetas
import json
from django.utils import timezone

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

        # ─── Validaciones ───────────────────────────────────────
        TIPOS_VALIDOS = {choice[0] for choice in MetaFinanciera._meta.get_field('tipo').choices}
        errores = []

        if not tipo or tipo not in TIPOS_VALIDOS:
            errores.append('Tipo de meta inválido.')

        try:
            objetivo_mensual_f = float(objetivo_mensual or 0)
            if objetivo_mensual_f <= 0:
                errores.append('El objetivo mensual debe ser mayor a cero.')
        except (ValueError, TypeError):
            errores.append('Objetivo mensual inválido.')
            objetivo_mensual_f = 0

        try:
            mes_i = int(mes or 0)
            if not (1 <= mes_i <= 12):
                errores.append('Mes inválido (debe ser entre 1 y 12).')
        except (ValueError, TypeError):
            errores.append('Mes inválido.')
            mes_i = 0

        try:
            anio_i = int(anio or 0)
            anio_actual = timezone.localdate().year
            if not (anio_actual - 5 <= anio_i <= anio_actual + 5):
                errores.append(f'Año fuera de rango (entre {anio_actual - 5} y {anio_actual + 5}).')
        except (ValueError, TypeError):
            errores.append('Año inválido.')
            anio_i = 0

        try:
            factor_f = float(factor_ajuste or 1.0)
            if not (0.1 <= factor_f <= 10.0):
                errores.append('Factor de ajuste fuera de rango (0.1 a 10.0).')
        except (ValueError, TypeError):
            errores.append('Factor de ajuste inválido.')
            factor_f = 1.0

        try:
            recordatorio_i = int(recordatorio_dias or 7)
            if not (0 <= recordatorio_i <= 30):
                errores.append('Días de recordatorio fuera de rango (0 a 30).')
        except (ValueError, TypeError):
            errores.append('Días de recordatorio inválido.')
            recordatorio_i = 7

        if errores:
            for err in errores:
                messages.error(request, err)
        else:
            try:
                meta_existente = MetaFinanciera.objects.filter(
                    empresa=empresa, tipo=tipo, mes=mes_i, anio=anio_i
                ).first()

                if meta_existente:
                    meta_existente.objetivo_mensual = objetivo_mensual_f
                    meta_existente.es_dinamica = es_dinamica
                    meta_existente.factor_ajuste = factor_f
                    meta_existente.recordatorio_dias = recordatorio_i
                    meta_existente.alertas_activas = alertas_activas
                    meta_existente.save()
                    messages.success(request, 'Meta actualizada exitosamente.')
                else:
                    MetaFinanciera.objects.create(
                        empresa=empresa, tipo=tipo,
                        objetivo_mensual=objetivo_mensual_f,
                        mes=mes_i, anio=anio_i,
                        es_dinamica=es_dinamica,
                        factor_ajuste=factor_f,
                        recordatorio_dias=recordatorio_i,
                        alertas_activas=alertas_activas
                    )
                    messages.success(request, 'Meta creada exitosamente.')

                return redirect('empresa:gestionar_metas')
            except Exception as e:
                messages.error(request, f'Error al guardar la meta: {str(e)}')

    # Obtener metas existentes — las propiedades son @cached_property,
    # se calculan UNA VEZ por instancia (no más N+1 en el template)
    metas = list(
        MetaFinanciera.objects.filter(empresa=empresa).order_by('-anio', '-mes')
    )
    
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
        'anios': range(2020, timezone.localdate().year + 2),
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
    """
    Obtiene datos mensuales con cálculo NIIF correcto:
    - Ventas: netas (sin IVA)
    - Costo de ventas: compras netas
    - Gastos: gastos operativos
    - Utilidad = ventas_netas − costo_ventas − gastos
    - Rentabilidad = utilidad / ventas_netas * 100
    """
    from empresa.models import Compra
    datos = []
    hoy = datetime.now()

    for i in range(meses - 1, -1, -1):
        mes = hoy.month - i
        anio = hoy.year
        while mes <= 0:
            mes += 12
            anio -= 1

        # Ventas netas
        ventas_qs = Venta.objects.filter(empresa=empresa, fecha__month=mes, fecha__year=anio)
        ventas_mes = (ventas_qs.aggregate(t=Sum('monto_neto'))['t']
                      or ventas_qs.aggregate(t=Sum('monto'))['t'] or 0)

        # Costo de ventas (compras del mes)
        compras_qs = Compra.objects.filter(empresa=empresa, fecha__month=mes, fecha__year=anio)
        costo_mes = (compras_qs.aggregate(t=Sum('monto_neto'))['t']
                     or compras_qs.aggregate(t=Sum('monto'))['t'] or 0)

        # Gastos operativos
        gastos_mes = Gasto.objects.filter(
            empresa=empresa, fecha__month=mes, fecha__year=anio
        ).aggregate(t=Sum('monto'))['t'] or 0

        utilidad = float(ventas_mes) - float(costo_mes) - float(gastos_mes)
        rentabilidad = (utilidad / float(ventas_mes) * 100) if float(ventas_mes) > 0 else 0

        datos.append({
            'mes': mes,
            'anio': anio,
            'ventas': ventas_mes,
            'costo_ventas': costo_mes,
            'gastos': gastos_mes,
            'utilidad': utilidad,
            'rentabilidad': round(rentabilidad, 1),
        })

    return datos


def calcular_benchmarking(empresa):
    """
    Estadísticas de benchmarking con cálculo NIIF consistente:
    Utilidad = ventas_netas − costo_ventas (compras) − gastos_operativos
    """
    from django.db.models import Avg, Count
    from empresa.models import Compra

    # Ventas netas (sin IVA)
    ventas_qs = Venta.objects.filter(empresa=empresa)
    ventas_netas = (ventas_qs.aggregate(t=Sum('monto_neto'))['t']
                    or ventas_qs.aggregate(t=Sum('monto'))['t'] or 0)
    promedio_ventas = (ventas_qs.aggregate(p=Avg('monto_neto'))['p']
                       or ventas_qs.aggregate(p=Avg('monto'))['p'] or 0)
    cantidad_ventas = ventas_qs.count()

    # Compras netas (costo de ventas) — sin IVA
    compras_qs = Compra.objects.filter(empresa=empresa)
    costo_ventas = (compras_qs.aggregate(t=Sum('monto_neto'))['t']
                    or compras_qs.aggregate(t=Sum('monto'))['t'] or 0)

    # Gastos operativos
    gastos_qs = Gasto.objects.filter(empresa=empresa)
    total_gastos = gastos_qs.aggregate(t=Sum('monto'))['t'] or 0
    promedio_gastos = gastos_qs.aggregate(p=Avg('monto'))['p'] or 0
    cantidad_gastos = gastos_qs.count()

    # Utilidad NIIF: ventas_netas − costo − gastos
    utilidad_total = float(ventas_netas) - float(costo_ventas) - float(total_gastos)

    # Margen sobre ventas netas
    margen_utilidad = 0
    if ventas_netas and float(ventas_netas) > 0:
        margen_utilidad = (utilidad_total / float(ventas_netas)) * 100

    return {
        'ventas_promedio_mensual': promedio_ventas,
        'gastos_promedio_mensual': promedio_gastos,
        'utilidad_total': utilidad_total,
        'margen_utilidad': margen_utilidad,
        'total_ventas': ventas_netas,
        'total_compras': costo_ventas,
        'total_gastos': total_gastos,
        'cantidad_ventas': cantidad_ventas,
        'cantidad_gastos': cantidad_gastos,
    }
