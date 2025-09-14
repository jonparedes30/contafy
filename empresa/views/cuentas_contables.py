# empresa/views/cuentas_contables.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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
            cuenta_data['monto_inicial'] = float(cuenta_data['monto_inicial'])  # Corregir serialización
            request.session['cuenta_data'] = cuenta_data

            
            # Obtener contrapartidas sugeridas (crear automáticamente si no existen)
            from empresa.services.accounting_setup import ensure_contrapartidas_for_account
            
            # Crear cuenta temporal para generar sugerencias
            cuenta_temp = CuentaContable(empresa=empresa, nombre=cuenta_data['nombre'], tipo=cuenta_data['tipo'])
            contrapartidas_creadas = ensure_contrapartidas_for_account(cuenta_temp)
            
            # Obtener cuentas existentes después de crear contrapartidas
            cuentas_existentes = CuentaContable.objects.filter(empresa=empresa).exclude(nombre=cuenta_data['nombre'])
            
            # Si aún no hay cuentas, crear las cuentas por defecto
            if not cuentas_existentes.exists():
                CuentasDefaultService.crear_cuentas_default(empresa)
                cuentas_existentes = CuentaContable.objects.filter(empresa=empresa).exclude(nombre=cuenta_data['nombre'])
            
            # Combinar con sugerencias del servicio existente
            contrapartidas_sugeridas = CuentasDefaultService.obtener_contrapartidas_sugeridas(
                cuenta_data['tipo'], empresa.categoria
            )
            
            # Agregar nombres de contrapartidas creadas automáticamente
            nombres_creadas = [c.nombre for c in contrapartidas_creadas]
            contrapartidas_sugeridas.extend(nombres_creadas)
            
            return render(request, 'empresa/partida_doble_confirmar.html', {
                'cuenta_data': cuenta_data,
                'cuentas': cuentas_existentes,
                'contrapartidas_sugeridas': list(set(contrapartidas_sugeridas)),  # Eliminar duplicados
            })
        else:
            messages.error(request, '❌ Corrige los errores en el formulario.')
    # Paso 2: Confirmación de partida doble
    elif request.method == 'POST' and request.POST.get('paso') == 'partida_doble':
        cuenta_data = request.session.get('cuenta_data')
        contrapartida_id = request.POST.get('contrapartida')
        contrapartida = CuentaContable.objects.filter(id=contrapartida_id, empresa=empresa).first()
        if not contrapartida:
            messages.error(request, 'Debes seleccionar una cuenta contrapartida válida.')
            cuentas = CuentaContable.objects.filter(empresa=empresa)
            return render(request, 'empresa/partida_doble_confirmar.html', {
                'cuenta_data': cuenta_data,
                'cuentas': cuentas,
                'error': 'Selecciona una cuenta contrapartida.'
            })
        # Validar y guardar partida doble
        with transaction.atomic():
            cuenta = CuentaContable.objects.create(
                empresa=empresa,
                nombre=cuenta_data['nombre'],
                tipo=cuenta_data['tipo']
            )
            monto = cuenta_data['monto_inicial']
            descripcion = f"Apertura de cuenta '{cuenta.nombre}' con contrapartida '{contrapartida.nombre}'"
            # Determinar debe/haber según tipo
            if cuenta.tipo in ['activo', 'gasto']:
                MovimientoContable.objects.create(
                    empresa=empresa, cuenta_fk=cuenta, cuenta_text=cuenta.nombre, tipo='debito', monto=monto, descripcion=descripcion
                )
                MovimientoContable.objects.create(
                    empresa=empresa, cuenta_fk=contrapartida, cuenta_text=contrapartida.nombre, tipo='credito', monto=monto, descripcion=descripcion
                )
            else:
                MovimientoContable.objects.create(
                    empresa=empresa, cuenta_fk=cuenta, cuenta_text=cuenta.nombre, tipo='credito', monto=monto, descripcion=descripcion
                )
                MovimientoContable.objects.create(
                    empresa=empresa, cuenta_fk=contrapartida, cuenta_text=contrapartida.nombre, tipo='debito', monto=monto, descripcion=descripcion
                )
            messages.success(request, '✅ Cuenta y asiento contable creados correctamente.')
            request.session.pop('cuenta_data', None)
            return redirect('empresa:dashboard')
    else:
        form = CuentaContableForm(empresa=empresa)

    return render(request, 'empresa/crear_cuenta_contable.html', {
        'form': form
    })

@login_required
def listar_cuentas_contables(request):
    empresa = request.user.empresa
    cuentas = CuentaContable.objects.filter(empresa=empresa).order_by('nombre')
    return render(request, 'empresa/listar_cuentas_contables.html', {
        'cuentas': cuentas
    })
