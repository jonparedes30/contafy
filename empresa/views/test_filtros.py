"""Vista de prueba para verificar filtros de fecha"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from ..services.filtros_service import FiltrosFechaService
from ..models import Venta, Gasto, Compra


@login_required
def test_filtros_fecha(request):
    """Vista para probar filtros de fecha"""
    empresa = request.user.empresa
    
    # Obtener rango de fechas
    fecha_inicio, fecha_fin = FiltrosFechaService.obtener_rango_fechas(request)
    
    # Validar fechas
    errores = FiltrosFechaService.validar_fechas(fecha_inicio, fecha_fin)
    
    if errores:
        return JsonResponse({
            'error': True,
            'errores': errores
        })
    
    # Obtener datos por período
    ventas_data = FiltrosFechaService.obtener_ventas_por_periodo(empresa, fecha_inicio, fecha_fin)
    gastos_data = FiltrosFechaService.obtener_gastos_por_periodo(empresa, fecha_inicio, fecha_fin)
    compras_data = FiltrosFechaService.obtener_compras_por_periodo(empresa, fecha_inicio, fecha_fin)
    
    # Obtener datos mensuales
    datos_mensuales = FiltrosFechaService.obtener_datos_mensuales(empresa, fecha_inicio, fecha_fin)
    
    # Obtener conteos para verificar
    total_ventas_registros = Venta.objects.filter(
        empresa=empresa,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).count()
    
    total_gastos_registros = Gasto.objects.filter(
        empresa=empresa,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).count()
    
    total_compras_registros = Compra.objects.filter(
        empresa=empresa,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).count()
    
    # Preparar respuesta
    resultado = {
        'filtros_aplicados': {
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
            'dias_rango': (fecha_fin - fecha_inicio).days + 1
        },
        'resumen_periodo': {
            'ventas_total': ventas_data['total'] or 0,
            'ventas_cantidad': ventas_data['cantidad'] or 0,
            'ventas_registros': total_ventas_registros,
            'gastos_total': gastos_data['total'] or 0,
            'gastos_registros': total_gastos_registros,
            'compras_total': compras_data['total'] or 0,
            'compras_registros': total_compras_registros
        },
        'datos_mensuales': datos_mensuales,
        'verificacion': {
            'filtros_funcionando': True,
            'datos_encontrados': total_ventas_registros + total_gastos_registros + total_compras_registros > 0
        }
    }
    
    if request.GET.get('format') == 'json':
        return JsonResponse(resultado)
    
    return render(request, 'empresa/test_filtros.html', {
        'resultado': resultado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    })


@login_required
def verificar_datos_fecha(request):
    """Vista para verificar datos específicos por fecha"""
    empresa = request.user.empresa
    fecha_str = request.GET.get('fecha')
    
    if not fecha_str:
        return JsonResponse({'error': 'Fecha requerida'})
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'})
    
    # Obtener datos específicos de esa fecha
    ventas_dia = Venta.objects.filter(
        empresa=empresa,
        fecha__date=fecha
    ).values('id', 'producto__nombre', 'cantidad', 'total', 'fecha')
    
    gastos_dia = Gasto.objects.filter(
        empresa=empresa,
        fecha__date=fecha
    ).values('id', 'descripcion', 'monto', 'fecha')
    
    compras_dia = Compra.objects.filter(
        empresa=empresa,
        fecha__date=fecha
    ).values('id', 'producto__nombre', 'cantidad', 'total', 'fecha')
    
    return JsonResponse({
        'fecha': fecha_str,
        'ventas': list(ventas_dia),
        'gastos': list(gastos_dia),
        'compras': list(compras_dia),
        'totales': {
            'ventas_count': len(ventas_dia),
            'gastos_count': len(gastos_dia),
            'compras_count': len(compras_dia)
        }
    })