from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from empresa.services.contabilidad_service import ContabilidadService
from empresa.models import CuentaPorCobrar, MovimientoInventario

@login_required
def dashboard_niif(request):
    """Dashboard de cumplimiento NIIF"""
    empresa = request.user.empresa
    
    # Estadísticas de cumplimiento
    cuentas_sin_deterioro = CuentaPorCobrar.objects.filter(
        empresa=empresa,
        estado='pendiente',
        deterioro_esperado=0
    ).count()
    
    total_cuentas = CuentaPorCobrar.objects.filter(
        empresa=empresa,
        estado='pendiente'
    ).count()
    
    movimientos_inventario = MovimientoInventario.objects.filter(
        empresa=empresa
    ).count()
    
    context = {
        'cuentas_sin_deterioro': cuentas_sin_deterioro,
        'total_cuentas': total_cuentas,
        'cumplimiento_deterioro': ((total_cuentas - cuentas_sin_deterioro) / total_cuentas * 100) if total_cuentas > 0 else 100,
        'movimientos_inventario': movimientos_inventario,
    }
    
    return render(request, 'empresa/niif/dashboard.html', context)

@login_required
def actualizar_deterioro_ajax(request):
    """Actualiza deterioro vía AJAX"""
    if request.method == 'POST':
        try:
            actualizadas = ContabilidadService.actualizar_deterioro_masivo(request.user.empresa)
            return JsonResponse({
                'success': True,
                'message': f'Se actualizaron {actualizadas} cuentas por cobrar',
                'actualizadas': actualizadas
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def reporte_cumplimiento_niif(request):
    """Reporte de cumplimiento NIIF completo"""
    from empresa.services.niif_service import NIIFService
    
    empresa = request.user.empresa
    
    # Generar reporte completo usando el servicio NIIF
    cumplimiento = NIIFService.generar_reporte_cumplimiento_niif(empresa)
    
    # Análisis detallado de cuentas por cobrar
    cuentas = CuentaPorCobrar.objects.filter(empresa=empresa, estado='pendiente')
    
    cuentas_data = []
    for cuenta in cuentas:
        cuentas_data.append({
            'cliente': cuenta.cliente.nombre,
            'monto': cuenta.monto_pendiente,
            'dias_vencido': cuenta.dias_vencido,
            'deterioro_actual': cuenta.deterioro_esperado,
            'deterioro_calculado': cuenta.calcular_deterioro_niif9(),
            'cumple_niif9': cuenta.deterioro_esperado == cuenta.calcular_deterioro_niif9()
        })
    
    context = {
        'cumplimiento': cumplimiento,
        'cuentas_data': cuentas_data,
        'total_deterioro': sum(c['deterioro_actual'] for c in cuentas_data),
        'cumplimiento_general': cumplimiento['puntuacion_general']
    }
    
    return render(request, 'empresa/niif/reporte_cumplimiento.html', context)

@login_required
def ejecutar_cierre_niif(request):
    """Ejecuta cierre contable según NIIF"""
    if request.method == 'POST':
        from empresa.services.niif_service import NIIFService
        
        try:
            resultados = NIIFService.ejecutar_cierre_niif(request.user.empresa)
            return JsonResponse({
                'success': True,
                'message': 'Cierre NIIF ejecutado correctamente',
                'resultados': resultados
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error en cierre NIIF: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def gestionar_contratos_niif15(request):
    """Gestión de contratos NIIF 15"""
    from empresa.models import ContratoVenta, ObligacionDesempeno
    
    empresa = request.user.empresa
    contratos = ContratoVenta.objects.filter(empresa=empresa).order_by('-fecha_inicio')
    
    context = {
        'contratos': contratos,
        'total_contratos': contratos.count(),
        'contratos_activos': contratos.filter(estado='activo').count(),
        'ingresos_pendientes': sum(
            o.precio_asignado for c in contratos 
            for o in c.obligaciones.filter(satisfecha=False)
        )
    }
    
    return render(request, 'empresa/niif/contratos_niif15.html', context)

@login_required
def estado_situacion_financiera_niif(request):
    """Estado de Situación Financiera según NIIF"""
    from empresa.services.reportes_niif_service import ReportesNIIFService
    
    empresa = request.user.empresa
    fecha_corte = request.GET.get('fecha_corte')
    
    if fecha_corte:
        from datetime import datetime
        fecha_corte = datetime.strptime(fecha_corte, '%Y-%m-%d').date()
    
    reporte = ReportesNIIFService.generar_estado_situacion_financiera(empresa, fecha_corte)
    
    context = {
        'reporte': reporte,
        'empresa': empresa
    }
    
    return render(request, 'empresa/niif/estado_situacion_financiera.html', context)

@login_required
def estado_resultados_niif(request):
    """Estado de Resultados según NIIF 15"""
    from empresa.services.reportes_niif_service import ReportesNIIFService
    from datetime import date, timedelta
    
    empresa = request.user.empresa
    
    # Fechas por defecto: mes actual
    fecha_fin = date.today()
    fecha_inicio = fecha_fin.replace(day=1)
    
    if request.GET.get('fecha_inicio'):
        from datetime import datetime
        fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
    if request.GET.get('fecha_fin'):
        from datetime import datetime
        fecha_fin = datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()
    
    reporte = ReportesNIIFService.generar_estado_resultados_niif(empresa, fecha_inicio, fecha_fin)
    
    context = {
        'reporte': reporte,
        'empresa': empresa,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    
    return render(request, 'empresa/niif/estado_resultados_niif.html', context)

@login_required
def notas_explicativas_niif(request):
    """Notas explicativas según NIIF"""
    from empresa.services.reportes_niif_service import ReportesNIIFService
    
    empresa = request.user.empresa
    notas = ReportesNIIFService.generar_notas_explicativas_niif(empresa)
    
    context = {
        'notas': notas,
        'empresa': empresa
    }
    
    return render(request, 'empresa/niif/notas_explicativas.html', context)

@login_required
def reporte_cumplimiento_completo(request):
    """Reporte completo de cumplimiento NIIF"""
    from empresa.services.reportes_niif_service import ReportesNIIFService
    
    empresa = request.user.empresa
    reporte_completo = ReportesNIIFService.generar_reporte_cumplimiento_completo(empresa)
    
    context = {
        'reporte': reporte_completo,
        'empresa': empresa
    }
    
    return render(request, 'empresa/niif/reporte_completo.html', context)