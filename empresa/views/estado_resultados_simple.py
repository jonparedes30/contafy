from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def estado_resultados_simple(request):
    return render(request, 'empresa/estado_resultado.html', {
        'ventas': 2500.00,
        'costos': 1200.00,
        'gastos': 600.00,
        'utilidad_bruta': 1300.00,
        'utilidad_operativa': 700.00,
        'utilidad_neta': 700.00,
        'fecha_inicio': datetime.now().replace(day=1).date(),
        'fecha_fin': datetime.now().date(),
        'formato_niif': False,
    })