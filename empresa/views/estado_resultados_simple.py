from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def estado_resultados_simple(request):
    # Verificar si se solicita formato NIIF
    formato_niif = request.GET.get('niif', 'false') == 'true'
    
    if formato_niif:
        # Datos de ejemplo para formato NIIF
        reporte_niif = {
            'ingresos_ordinarios': {
                'Ventas de productos': 2500.00,
                'Servicios prestados': 300.00,
            },
            'costos_ventas': {
                'Costo de mercaderías': 1200.00,
                'Mano de obra directa': 200.00,
            },
            'gastos_operativos': {
                'Gastos administrativos': 400.00,
                'Gastos de ventas': 200.00,
            },
            'totales': {
                'ingresos_ordinarios': 2800.00,
                'costos_ventas': 1400.00,
                'utilidad_bruta': 1400.00,
                'gastos_operativos': 600.00,
                'utilidad_neta': 800.00,
            }
        }
        
        context = {
            'reporte_niif': reporte_niif,
            'formato_niif': True,
            'fecha_inicio': datetime.now().replace(day=1).date(),
            'fecha_fin': datetime.now().date(),
        }
    else:
        # Vista tradicional
        context = {
            'ventas': 2500.00,
            'costos': 1200.00,
            'gastos': 600.00,
            'utilidad_bruta': 1300.00,
            'utilidad_operativa': 700.00,
            'utilidad_neta': 700.00,
            'fecha_inicio': datetime.now().replace(day=1).date(),
            'fecha_fin': datetime.now().date(),
            'formato_niif': False,
        }
    
    return render(request, 'empresa/estado_resultado.html', context)