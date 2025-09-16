# empresa/views/cuentas_contables.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from empresa.forms import CuentaContableForm
from empresa.models import CuentaContable, MovimientoContable
from empresa.services.cuentas_default_service import CuentasDefaultService
from django.db import transaction

@login_required
def crear_cuenta_contable(request):
    empresa = request.user.empresa
    
    if request.method == 'POST':
        form = CuentaContableForm(request.POST, empresa=empresa)
        if form.is_valid():
            cuenta = form.save(commit=False)
            cuenta.empresa = empresa
            cuenta.save()
            
            messages.success(request, f'Cuenta "{cuenta.nombre}" creada exitosamente.')
            return redirect('empresa:listar_cuentas_contables')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CuentaContableForm(empresa=empresa)

    return render(request, 'empresa/crear_cuenta_contable.html', {
        'form': form
    })

@login_required
def listar_cuentas_contables(request):
    empresa = request.user.empresa
    cuentas = list(CuentaContable.objects.filter(empresa=empresa).order_by('nombre'))
    
    # Agregar cuentas virtuales del capital
    from empresa.models import Capital
    capital_aportes = Capital.objects.filter(empresa=empresa, tipo='aporte').aggregate(total=Sum('monto'))['total'] or 0
    capital_retiros = Capital.objects.filter(empresa=empresa, tipo='retiro').aggregate(total=Sum('monto'))['total'] or 0
    capital_neto = capital_aportes - capital_retiros
    
    if capital_neto > 0:
        # Crear objetos virtuales para mostrar en la lista
        class CuentaVirtual:
            def __init__(self, nombre, tipo, valor):
                self.nombre = nombre
                self.tipo = tipo
                self.valor = valor
                self.id = f'virtual_{nombre.lower().replace(" ", "_")}'
        
        cuentas.append(CuentaVirtual('Caja (Capital)', 'activo', capital_neto))
        cuentas.append(CuentaVirtual('Capital Social', 'capital', capital_neto))
    
    return render(request, 'empresa/listar_cuentas_contables.html', {
        'cuentas': cuentas
    })
