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
            from django.db import transaction
            from empresa.models import CuentaContable, MovimientoContable
            import uuid
            
            try:
                with transaction.atomic():
                    capital = form.save(commit=False)
                    capital.empresa = request.user.empresa
                    capital.creado_por = request.user
                    
                    # Truncar descripción si es muy larga
                    if len(capital.descripcion) > 100:
                        capital.descripcion = capital.descripcion[:97] + '...'
                    
                    capital.save()
                    
                    # Crear cuentas básicas si no existen
                    cuenta_caja, _ = CuentaContable.objects.get_or_create(
                        empresa=request.user.empresa,
                        nombre='Caja',
                        defaults={'tipo': 'activo'}
                    )
                    
                    cuenta_capital, _ = CuentaContable.objects.get_or_create(
                        empresa=request.user.empresa,
                        nombre='Capital',
                        defaults={'tipo': 'capital'}
                    )
                    
                    # Crear asientos contables manualmente
                    transaccion_id = str(uuid.uuid4())[:8]
                    descripcion = capital.descripcion
                    
                    # Debug: Verificar que las cuentas se crearon
                    print(f"DEBUG: Cuenta Caja creada - ID: {cuenta_caja.id}, Nombre: {cuenta_caja.nombre}")
                    print(f"DEBUG: Cuenta Capital creada - ID: {cuenta_capital.id}, Nombre: {cuenta_capital.nombre}")
                    
                    if capital.tipo == 'aporte':
                        # Débito: Caja (Activo aumenta)
                        MovimientoContable.objects.create(
                            empresa=request.user.empresa,
                            cuenta_fk=cuenta_caja,
                            cuenta_text='Caja',
                            tipo='debito',
                            monto=capital.monto,
                            descripcion=descripcion,
                            estado='confirmado',
                            transaccion_id=transaccion_id
                        )
                        
                        # Crédito: Capital (Capital aumenta)
                        mov_credito = MovimientoContable.objects.create(
                            empresa=request.user.empresa,
                            cuenta_fk=cuenta_capital,
                            cuenta_text='Capital',
                            tipo='credito',
                            monto=capital.monto,
                            descripcion=descripcion,
                            estado='confirmado',
                            transaccion_id=transaccion_id
                        )
                        
                        # Debug: Verificar que los asientos se crearon
                        print(f"DEBUG: Asiento crédito creado - ID: {mov_credito.id}, Monto: {mov_credito.monto}")
                        
                        # Verificar total de movimientos
                        total_movimientos = MovimientoContable.objects.filter(empresa=request.user.empresa).count()
                        print(f"DEBUG: Total movimientos en BD: {total_movimientos}")
                    else:  # retiro
                        # Débito: Capital (Capital disminuye)
                        MovimientoContable.objects.create(
                            empresa=request.user.empresa,
                            cuenta_fk=cuenta_capital,
                            cuenta_text='Capital',
                            tipo='debito',
                            monto=capital.monto,
                            descripcion=descripcion,
                            estado='confirmado',
                            transaccion_id=transaccion_id
                        )
                        
                        # Crédito: Caja (Activo disminuye)
                        mov_credito = MovimientoContable.objects.create(
                            empresa=request.user.empresa,
                            cuenta_fk=cuenta_caja,
                            cuenta_text='Caja',
                            tipo='credito',
                            monto=capital.monto,
                            descripcion=descripcion,
                            estado='confirmado',
                            transaccion_id=transaccion_id
                        )
                        
                        # Debug: Verificar que los asientos se crearon
                        print(f"DEBUG: Asiento crédito creado - ID: {mov_credito.id}, Monto: {mov_credito.monto}")
                        
                        # Verificar total de movimientos
                        total_movimientos = MovimientoContable.objects.filter(empresa=request.user.empresa).count()
                        print(f"DEBUG: Total movimientos en BD: {total_movimientos}")
                    
                    tipo_texto = "aporte" if capital.tipo == 'aporte' else "retiro"
                    messages.success(request, f'{tipo_texto.title()} de capital registrado: ${capital.monto} (con asientos contables)')
                    return redirect('empresa:listar_capital')
                    
            except Exception as e:
                messages.error(request, f'Error al registrar capital: {str(e)}')
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