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
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        logger.info(f"POST data recibido: {request.POST}")
        
        form = CapitalForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            try:
                logger.info(f"Formulario válido. Datos: {form.cleaned_data}")
                
                capital = form.save(commit=False)
                capital.empresa = request.user.empresa
                capital.creado_por = request.user
                
                logger.info(f"Capital antes de save: monto={capital.monto}, tipo={capital.tipo}, descripcion='{capital.descripcion}' (len={len(capital.descripcion)})")
                
                capital.save()  # Los asientos contables se crean automáticamente
                
                logger.info(f"Capital guardado exitosamente: ID={capital.id}")
                
                tipo_texto = "aporte" if capital.tipo == 'aporte' else "retiro"
                messages.success(request, f'{tipo_texto.title()} de capital registrado: ${capital.monto}')
                return redirect('empresa:listar_capital')
                
            except Exception as e:
                logger.error(f"Error al guardar capital: {str(e)}")
                logger.error(f"Tipo de error: {type(e).__name__}")
                messages.error(request, f'Error al registrar capital: {str(e)}')
        else:
            logger.error(f"Formulario inválido. Errores: {form.errors}")
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