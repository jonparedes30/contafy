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

    # Paso 1: Formulario principal
    if request.method == 'POST' and 'paso' not in request.POST:
        form = CuentaContableForm(request.POST, empresa=empresa)
        if form.is_valid():
            cuenta_data = form.cleaned_data.copy()
            cuenta_data['monto_inicial'] = float(cuenta_data['monto_inicial'])
            request.session['cuenta_data'] = cuenta_data

            # Obtener cuentas existentes
            cuentas_existentes = CuentaContable.objects.filter(empresa=empresa)
            
            # Si no hay cuentas, crear las básicas
            if not cuentas_existentes.exists():
                CuentasDefaultService.crear_cuentas_default(empresa)
                cuentas_existentes = CuentaContable.objects.filter(empresa=empresa)
            
            # Sugerencias de contrapartidas según tipo de cuenta
            contrapartidas_sugeridas = {
                'activo': ['Capital', 'Cuentas por Pagar', 'Préstamos Bancarios'],
                'pasivo': ['Caja', 'Bancos', 'Capital'],
                'capital': ['Caja', 'Bancos', 'Activos Fijos'],
                'ingreso': ['Caja', 'Bancos', 'Cuentas por Cobrar'],
                'gasto': ['Caja', 'Bancos', 'Cuentas por Pagar']
            }.get(cuenta_data['tipo'], ['Caja', 'Capital'])
            
            return render(request, 'empresa/partida_doble_confirmar.html', {
                'cuenta_data': cuenta_data,
                'cuentas': cuentas_existentes,
                'contrapartidas_sugeridas': contrapartidas_sugeridas,
            })
        else:
            messages.error(request, '❌ Corrige los errores en el formulario.')
    # Paso 2: Confirmación de partida doble
    elif request.method == 'POST' and request.POST.get('paso') == 'partida_doble':
        cuenta_data = request.session.get('cuenta_data')
        contrapartida_id = request.POST.get('contrapartida')
        nueva_contrapartida = request.POST.get('nueva_contrapartida', '').strip()
        
        # Determinar contrapartida (existente o nueva)
        if contrapartida_id:
            contrapartida = CuentaContable.objects.filter(id=contrapartida_id, empresa=empresa).first()
        elif nueva_contrapartida:
            # Crear nueva cuenta contrapartida
            tipo_contrapartida = 'activo' if cuenta_data['tipo'] in ['pasivo', 'capital'] else 'capital'
            contrapartida = CuentaContable.objects.create(
                empresa=empresa,
                nombre=nueva_contrapartida,
                tipo=tipo_contrapartida
            )
        else:
            contrapartida = None
            
        if not contrapartida:
            messages.error(request, 'Debes seleccionar o crear una cuenta contrapartida.')
            cuentas = CuentaContable.objects.filter(empresa=empresa)
            return render(request, 'empresa/partida_doble_confirmar.html', {
                'cuenta_data': cuenta_data,
                'cuentas': cuentas,
            })
            
        # Crear cuenta y asientos con estado
        with transaction.atomic():
            import uuid
            transaccion_id = str(uuid.uuid4())[:8]
            
            cuenta = CuentaContable.objects.create(
                empresa=empresa,
                nombre=cuenta_data['nombre'],
                tipo=cuenta_data['tipo'],
                monto_inicial=cuenta_data['monto_inicial']
            )
            
            monto = cuenta_data['monto_inicial']
            descripcion = f"Apertura cuenta: {cuenta.nombre}"
            
            # Crear asientos con estado confirmado
            if cuenta.tipo in ['activo', 'gasto']:
                MovimientoContable.objects.create(
                    empresa=empresa, cuenta_fk=cuenta, cuenta_text=cuenta.nombre, 
                    tipo='debito', monto=monto, descripcion=descripcion,
                    estado='confirmado', transaccion_id=transaccion_id
                )
                MovimientoContable.objects.create(
                    empresa=empresa, cuenta_fk=contrapartida, cuenta_text=contrapartida.nombre, 
                    tipo='credito', monto=monto, descripcion=descripcion,
                    estado='confirmado', transaccion_id=transaccion_id
                )
            else:
                MovimientoContable.objects.create(
                    empresa=empresa, cuenta_fk=cuenta, cuenta_text=cuenta.nombre, 
                    tipo='credito', monto=monto, descripcion=descripcion,
                    estado='confirmado', transaccion_id=transaccion_id
                )
                MovimientoContable.objects.create(
                    empresa=empresa, cuenta_fk=contrapartida, cuenta_text=contrapartida.nombre, 
                    tipo='debito', monto=monto, descripcion=descripcion,
                    estado='confirmado', transaccion_id=transaccion_id
                )
                
            messages.success(request, f'✅ Cuenta "{cuenta.nombre}" creada con asiento contable confirmado.')
            request.session.pop('cuenta_data', None)
            return redirect('empresa:listar_cuentas_contables')
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
