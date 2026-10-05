# empresa/views/capital.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from empresa.models import Capital
from empresa.forms import CapitalForm
from empresa.decorators import require_power
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from empresa.services.capital_service import registrar_asiento_capital
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
@require_power('puede_gestionar_cuentas')
def crear_capital(request):
    if request.method == 'POST':
        form = CapitalForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            capital = form.save(commit=False)
            capital.empresa = request.user.empresa
            capital.creado_por = request.user
            
            if len(capital.descripcion) > 100:
                capital.descripcion = capital.descripcion[:97] + '...'

            # El asiento se registra aquí (y no en Capital.save) para que el
            # aporte/retiro aparezca en el Balance sin recursión de señales.
            with transaction.atomic():
                capital.save()
                registrar_asiento_capital(capital)

            tipo_texto = "aporte" if capital.tipo == 'aporte' else "retiro"
            messages.success(request, f'{tipo_texto.title()} de capital registrado: ${capital.monto}')
            return redirect('empresa:listar_capital')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')
    else:
        form = CapitalForm(empresa=request.user.empresa)
    
    return render(request, 'empresa/crear_capital.html', {'form': form})

@login_required
@require_power('puede_gestionar_cuentas')
def listar_capital(request):
    empresa = request.user.empresa
    movimientos_capital = Capital.objects.filter(empresa=empresa).order_by('-fecha')
    
    total_aportes = movimientos_capital.filter(tipo='aporte').aggregate(total=Sum('monto'))['total'] or 0
    total_retiros = movimientos_capital.filter(tipo='retiro').aggregate(total=Sum('monto'))['total'] or 0
    capital_neto = total_aportes - total_retiros
    
    # Paginación: 15 registros por página
    paginator = Paginator(movimientos_capital, 15)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    contexto = {
        'page_obj': page_obj,
        'movimientos_capital': page_obj.object_list,
        'total_aportes': total_aportes,
        'total_retiros': total_retiros,
        'capital_neto': capital_neto,
    }
    return render(request, 'empresa/listar_capital.html', contexto)