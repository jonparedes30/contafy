from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.db.models import Sum
from empresa.models import Venta, Gasto

@login_required
def estado_resultados_simple(request):
    empresa = request.user.empresa
    
    # Obtener fechas del request o usar valores por defecto
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    
    if fecha_inicio_str and fecha_fin_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_inicio = datetime.now().replace(day=1).date()
            fecha_fin = datetime.now().date()
    else:
        fecha_inicio = datetime.now().replace(day=1).date()
        fecha_fin = datetime.now().date()
    
    # Calcular totales usando datos reales de Fatima
    ventas_total = Venta.objects.filter(
        empresa=empresa,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    gastos_total = Gasto.objects.filter(
        empresa=empresa,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    utilidad_neta = ventas_total - gastos_total
    
    # Verificar si se solicita formato NIIF
    formato_niif = request.GET.get('niif', 'false') == 'true'
    
    if formato_niif:
        # Para NIIF, usar los mismos datos reales pero estructurados
        reporte_niif = {
            'ingresos_ordinarios': {
                'Ventas': ventas_total,
            },
            'costos_ventas': {},  # No hay costos separados por ahora
            'gastos_operativos': {
                'Gastos Operativos': gastos_total,
            },
            'totales': {
                'ingresos_ordinarios': ventas_total,
                'costos_ventas': 0,
                'utilidad_bruta': ventas_total,
                'gastos_operativos': gastos_total,
                'utilidad_neta': utilidad_neta,
            }
        }
        
        context = {
            'reporte_niif': reporte_niif,
            'formato_niif': True,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
        }
    else:
        # Vista tradicional con datos reales
        context = {
            'ventas': float(ventas_total),
            'costos': 0,  # No hay costos separados por ahora
            'gastos': float(gastos_total),
            'utilidad_bruta': float(ventas_total),
            'utilidad_operativa': float(utilidad_neta),
            'utilidad_neta': float(utilidad_neta),
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'formato_niif': False,
        }
    
    return render(request, 'empresa/estado_resultado.html', context)