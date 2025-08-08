from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from empresa.services.valuacion_service import ServicioValuacion

@login_required
def valuacion_empresa(request):
    """Vista para mostrar la valuación de la empresa"""
    empresa = request.user.empresa
    
    # Calcular valuación completa
    valuacion = ServicioValuacion.calcular_valuacion_completa(empresa)
    
    # Proyecciones futuras
    proyecciones = ServicioValuacion.proyectar_valor_futuro(empresa, años=5)
    
    return render(request, 'empresa/valuacion.html', {
        'valuacion': valuacion,
        'proyecciones': proyecciones,
        'empresa': empresa
    })