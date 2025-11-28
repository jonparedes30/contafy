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
        form = GastoForm(request.POST)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.empresa = request.user.empresa
            gasto.creado_por = request.user
            gasto.save()
            return redirect('empresa:home')
    else:
        form = GastoForm()
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

    es_propietario = not hasattr(request.user, 'poderes') or request.user.is_superuser
    
    contexto = {
        'gastos': gastos,
        'total_gastos': total_gastos,
        'total_transacciones': total_transacciones,
        'promedio_gasto': promedio_gasto,
        'es_propietario': es_propietario,
    }
    return render(request, 'empresa/listar_gastos.html', contexto)

@login_required
def editar_gasto(request, gasto_id):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    
    if hasattr(request.user, 'poderes') and not request.user.is_superuser:
        messages.error(request, 'Solo el propietario puede editar gastos.')
        return redirect('empresa:listar_gastos')
    
    empresa = request.user.empresa
    gasto = get_object_or_404(Gasto, id=gasto_id, empresa=empresa)
    
    if request.method == 'POST':
        try:
            gasto.descripcion = request.POST.get('descripcion', gasto.descripcion)
            gasto.monto = float(request.POST.get('monto', gasto.monto))
            gasto.categoria = request.POST.get('categoria', gasto.categoria)
            gasto.save()
            
            messages.success(request, 'Gasto actualizado correctamente.')
            return redirect('empresa:listar_gastos')
        except Exception as e:
            messages.error(request, f'Error al actualizar gasto: {str(e)}')
    
    context = {'gasto': gasto}
    return render(request, 'empresa/editar_gasto.html', context)

@login_required
def eliminar_gasto(request, gasto_id):
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    from django.contrib import messages
    
    if hasattr(request.user, 'poderes') and not request.user.is_superuser:
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if request.method == 'POST':
        try:
            empresa = request.user.empresa
            gasto = get_object_or_404(Gasto, id=gasto_id, empresa=empresa)
            gasto.delete()
            
            messages.success(request, 'Gasto eliminado correctamente.')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
