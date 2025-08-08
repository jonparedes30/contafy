from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from empresa.models import Gasto
from empresa.forms import GastoForm
from empresa.decorators import require_power
from django.db.models import Sum, Avg, Count, Q
from empresa.views.contabilidad import registrar_movimiento_contable

@login_required
@require_power('puede_registrar_gastos')
def crear_gasto(request):
    if request.method == 'POST':
        form = GastoForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.empresa = request.user.empresa
            gasto.creado_por = request.user
            gasto.save()  # Los asientos contables se crean automáticamente en el modelo
            return redirect('empresa:home')
    else:
        form = GastoForm(empresa=request.user.empresa)
    return render(request, 'empresa/crear_gasto.html', {'form': form})

@login_required
@require_power('puede_registrar_gastos')
def listar_gastos(request):
    empresa = request.user.empresa
    gastos = Gasto.objects.filter(empresa=empresa).order_by('-fecha')

    # Filtros avanzados
    buscar = request.GET.get('buscar', '').strip()
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    monto = request.GET.get('monto')
    categoria = request.GET.get('categoria')

    if buscar:
        gastos = gastos.filter(
            Q(descripcion__icontains=buscar) |
            Q(categoria__icontains=buscar)
        )
    if fecha_desde:
        gastos = gastos.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        gastos = gastos.filter(fecha__date__lte=fecha_hasta)
    if monto:
        if '-' in monto:
            min_monto, max_monto = monto.split('-')
            gastos = gastos.filter(monto__gte=float(min_monto), monto__lte=float(max_monto))
        elif monto.endswith('+'):
            min_monto = monto.replace('+', '')
            gastos = gastos.filter(monto__gte=float(min_monto))
    if categoria:
        gastos = gastos.filter(categoria=categoria)

    # Estadísticas generales
    total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or 0
    total_transacciones = gastos.count()
    promedio_gasto = gastos.aggregate(promedio=Avg('monto'))['promedio'] or 0

    contexto = {
        'gastos': gastos,
        'total_gastos': total_gastos,
        'total_transacciones': total_transacciones,
        'promedio_gasto': promedio_gasto,
    }
    return render(request, 'empresa/listar_gastos.html', contexto)
