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
        logger.info(f"POST recibido para crear capital. Usuario: {request.user}, Empresa: {request.user.empresa}")
        logger.info(f"Datos POST: {request.POST}")
        
        form = CapitalForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            try:
                logger.info(f"Formulario válido. Datos: {form.cleaned_data}")
                
                capital = form.save(commit=False)
                capital.empresa = request.user.empresa
                capital.creado_por = request.user
                
                logger.info(f"Capital antes de save: monto={capital.monto}, tipo={capital.tipo}, empresa={capital.empresa}")
                
                # Truncar descripción antes de guardar
                if len(capital.descripcion) > 100:
                    capital.descripcion = capital.descripcion[:97] + '...'
                
                capital.save()
                logger.info(f"Capital guardado exitosamente. ID: {capital.id}")
                
                # Verificar que se guardó correctamente
                capital_verificacion = Capital.objects.get(id=capital.id)
                logger.info(f"Verificación - Capital en BD: ID={capital_verificacion.id}, Monto={capital_verificacion.monto}")
                
                tipo_texto = "aporte" if capital.tipo == 'aporte' else "retiro"
                messages.success(request, f'{tipo_texto.title()} de capital registrado: ${capital.monto}')
                return redirect('empresa:listar_capital')
                
            except Exception as e:
                logger.error(f"Error guardando capital: {str(e)}")
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
    import logging
    logger = logging.getLogger(__name__)
    
    empresa = request.user.empresa
    logger.info(f"Listando capital para empresa: {empresa}")
    
    movimientos_capital = Capital.objects.filter(empresa=empresa).order_by('-fecha')
    logger.info(f"Movimientos encontrados: {movimientos_capital.count()}")
    
    for mov in movimientos_capital:
        logger.info(f"Capital ID: {mov.id}, Monto: {mov.monto}, Tipo: {mov.tipo}, Fecha: {mov.fecha}")
    
    # Estadísticas
    total_aportes = movimientos_capital.filter(tipo='aporte').aggregate(total=Sum('monto'))['total'] or 0
    total_retiros = movimientos_capital.filter(tipo='retiro').aggregate(total=Sum('monto'))['total'] or 0
    capital_neto = total_aportes - total_retiros
    
    logger.info(f"Estadísticas - Aportes: {total_aportes}, Retiros: {total_retiros}, Neto: {capital_neto}")
    
    contexto = {
        'movimientos_capital': movimientos_capital,
        'total_aportes': total_aportes,
        'total_retiros': total_retiros,
        'capital_neto': capital_neto,
    }
    return render(request, 'empresa/listar_capital.html', contexto)