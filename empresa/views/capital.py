# empresa/views/capital.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from empresa.models import Capital
from empresa.forms import CapitalForm
from empresa.decorators import require_power
from django.contrib import messages
from django.db.models import Sum

@login_required
@require_power('puede_gestionar_cuentas')
def crear_capital(request):
    if request.method == 'POST':
        form = CapitalForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            capital = form.save(commit=False)
            capital.empresa = request.user.empresa
            capital.creado_por = request.user
            
            # Truncar descripción si es muy larga
            if len(capital.descripcion) > 100:
                capital.descripcion = capital.descripcion[:97] + '...'
            
            capital.save()
            
            # Crear asientos contables usando la función existente
            try:
                from empresa.views.contabilidad import registrar_movimiento_contable
                
                if capital.tipo == 'aporte':
                    # Aporte: Caja (Débito) / Capital (Crédito)
                    registrar_movimiento_contable(
                        empresa=request.user.empresa,
                        cuenta_debito_nombre='Caja',
                        cuenta_credito_nombre='Capital',
                        monto=capital.monto,
                        descripcion=capital.descripcion,
                        tipo_cuenta_debito='activo',
                        tipo_cuenta_credito='capital'
                    )
                else:
                    # Retiro: Capital (Débito) / Caja (Crédito)
                    registrar_movimiento_contable(
                        empresa=request.user.empresa,
                        cuenta_debito_nombre='Capital',
                        cuenta_credito_nombre='Caja',
                        monto=capital.monto,
                        descripcion=capital.descripcion,
                        tipo_cuenta_debito='capital',
                        tipo_cuenta_credito='activo'
                    )
                
                tipo_texto = "aporte" if capital.tipo == 'aporte' else "retiro"
                messages.success(request, f'{tipo_texto.title()} de capital registrado: ${capital.monto}')
                
            except Exception as e:
                messages.warning(request, f'Capital registrado, pero error en asientos: {str(e)}')
            
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
    
    # Estadísticas
    total_aportes = movimientos_capital.filter(tipo='aporte').aggregate(total=Sum('monto'))['total'] or 0
    total_retiros = movimientos_capital.filter(tipo='retiro').aggregate(total=Sum('monto'))['total'] or 0
    capital_neto = total_aportes - total_retiros
    
    contexto = {
        'movimientos_capital': movimientos_capital,
        'total_aportes': total_aportes,
        'total_retiros': total_retiros,
        'capital_neto': capital_neto,
    }
    return render(request, 'empresa/listar_capital.html', contexto)