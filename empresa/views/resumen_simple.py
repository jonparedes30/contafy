from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def resumen_financiero_simple(request):
    """Vista simplificada del resumen financiero que no falla"""
    try:
        empresa = request.user.empresa
        
        # Datos básicos simulados para evitar errores
        context = {
            'ventas': 0,
            'compras': 0,
            'gastos': 0,
            'utilidad_bruta': 0,
            'utilidad_neta': 0,
            'recomendaciones': [{
                'tipo': 'info',
                'titulo': 'Sistema en mantenimiento',
                'descripcion': 'El resumen financiero está siendo optimizado. Usa el dashboard principal para ver tus datos.'
            }],
            'conclusion': {
                'estado': 'info',
                'titulo': 'Resumen simplificado',
                'descripcion': 'Vista temporal mientras se optimiza el sistema completo.'
            },
            'roe': 0,
            'liquidez': 0,
            'endeudamiento': 0,
            'margen_neto': 0,
            'margen_bruto': 0,
            'ratio_gastos_ventas': 0,
            'ratio_costos': 0,
            'rotacion_activos': 0,
            'analisis_predictivo': {}
        }
        
        return render(request, 'empresa/resumen_simple.html', context)
        
    except Exception as e:
        return HttpResponse(f'Error temporal en resumen: {str(e)}. Usa el dashboard principal.', status=200)