# empresa/views/cuentas_contables.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from empresa.forms import CuentaContableForm
from empresa.models import CuentaContable, MovimientoContable
from empresa.services.cuentas_default_service import CuentasDefaultService
from django.db import transaction
from empresa.models import MovimientoContable

@login_required
def crear_cuenta_contable(request):
    empresa = request.user.empresa
    
    # Paso 1: Formulario inicial
    if request.method == 'POST' and 'paso' not in request.POST:
        nombre = request.POST.get('nombre', '').strip()
        tipo = request.POST.get('tipo', '')
        monto_inicial = request.POST.get('monto_inicial', '0')
        
        if nombre and tipo:
            try:
                monto_inicial = float(monto_inicial)
                # Guardar datos en sesión
                request.session['cuenta_data'] = {
                    'nombre': nombre,
                    'tipo': tipo,
                    'monto_inicial': monto_inicial
                }
                
                # Obtener cuentas existentes para contrapartida
                cuentas = CuentaContable.objects.filter(empresa=empresa)
                
                # Sugerencias inteligentes según el tipo de cuenta
                sugerencias = {
                    'activo': [
                        {'nombre': 'Capital', 'descripcion': 'Aporte de los socios o propietario'},
                        {'nombre': 'Préstamo Bancario', 'descripcion': 'Dinero prestado por el banco'},
                        {'nombre': 'Cuentas por Pagar', 'descripcion': 'Dinero que debes a proveedores'},
                        {'nombre': 'Bancos', 'descripcion': 'Transferencia entre cuentas bancarias'}
                    ],
                    'pasivo': [
                        {'nombre': 'Caja', 'descripcion': 'Dinero en efectivo recibido'},
                        {'nombre': 'Bancos', 'descripcion': 'Dinero depositado en el banco'},
                        {'nombre': 'Equipos', 'descripcion': 'Compra de equipos a crédito'}
                    ],
                    'capital': [
                        {'nombre': 'Caja', 'descripcion': 'Aporte en efectivo'},
                        {'nombre': 'Bancos', 'descripcion': 'Aporte depositado en banco'},
                        {'nombre': 'Equipos', 'descripcion': 'Aporte de equipos o activos'}
                    ],
                    'ingreso': [
                        {'nombre': 'Caja', 'descripcion': 'Cobro en efectivo'},
                        {'nombre': 'Bancos', 'descripcion': 'Cobro por transferencia'},
                        {'nombre': 'Cuentas por Cobrar', 'descripcion': 'Venta a crédito'}
                    ],
                    'gasto': [
                        {'nombre': 'Caja', 'descripcion': 'Pago en efectivo'},
                        {'nombre': 'Bancos', 'descripcion': 'Pago por transferencia'},
                        {'nombre': 'Cuentas por Pagar', 'descripcion': 'Compra a crédito'}
                    ]
                }
                
                contrapartidas_sugeridas = sugerencias.get(tipo, [])
                
                return render(request, 'empresa/partida_doble_confirmar.html', {
                    'cuenta_data': request.session['cuenta_data'],
                    'cuentas': cuentas,
                    'contrapartidas_sugeridas': contrapartidas_sugeridas,
                })
            except ValueError:
                messages.error(request, 'El monto inicial debe ser un número válido.')
        else:
            messages.error(request, 'Nombre y tipo son obligatorios.')
    
    # Paso 2: Confirmar partida doble
    elif request.method == 'POST' and request.POST.get('paso') == 'partida_doble':
        cuenta_data = request.session.get('cuenta_data')
        if not cuenta_data:
            messages.error(request, 'Datos de cuenta no encontrados. Intenta nuevamente.')
            return redirect('empresa:crear_cuenta_contable')
        
        contrapartida_id = request.POST.get('contrapartida')
        nueva_contrapartida = request.POST.get('nueva_contrapartida', '').strip()
        
        # Crear la cuenta principal
        cuenta = CuentaContable.objects.create(
            empresa=empresa,
            nombre=cuenta_data['nombre'],
            tipo=cuenta_data['tipo'],
            monto_inicial=cuenta_data['monto_inicial']
        )
        
        # Crear asientos si hay monto inicial
        if cuenta_data['monto_inicial'] > 0:
            if contrapartida_id:
                contrapartida = CuentaContable.objects.get(id=contrapartida_id, empresa=empresa)
            elif nueva_contrapartida:
                tipo_contrapartida = 'capital' if cuenta_data['tipo'] == 'activo' else 'activo'
                contrapartida = CuentaContable.objects.create(
                    empresa=empresa,
                    nombre=nueva_contrapartida,
                    tipo=tipo_contrapartida
                )
            else:
                # Crear contrapartida por defecto
                contrapartida = CuentaContable.objects.get_or_create(
                    empresa=empresa,
                    nombre='Capital',
                    defaults={'tipo': 'capital'}
                )[0]
            
            # Crear movimientos contables
            import uuid
            transaccion_id = str(uuid.uuid4())[:8]
            
            if cuenta.tipo in ['activo', 'gasto']:
                # Débito en la cuenta nueva
                MovimientoContable.objects.create(
                    empresa=empresa,
                    cuenta_fk=cuenta,
                    cuenta_text=cuenta.nombre,
                    tipo='debito',
                    monto=cuenta_data['monto_inicial'],
                    descripcion=f'Apertura cuenta {cuenta.nombre}',
                    transaccion_id=transaccion_id
                )
                # Crédito en contrapartida
                MovimientoContable.objects.create(
                    empresa=empresa,
                    cuenta_fk=contrapartida,
                    cuenta_text=contrapartida.nombre,
                    tipo='credito',
                    monto=cuenta_data['monto_inicial'],
                    descripcion=f'Apertura cuenta {cuenta.nombre}',
                    transaccion_id=transaccion_id
                )
            else:
                # Crédito en la cuenta nueva
                MovimientoContable.objects.create(
                    empresa=empresa,
                    cuenta_fk=cuenta,
                    cuenta_text=cuenta.nombre,
                    tipo='credito',
                    monto=cuenta_data['monto_inicial'],
                    descripcion=f'Apertura cuenta {cuenta.nombre}',
                    transaccion_id=transaccion_id
                )
                # Débito en contrapartida
                MovimientoContable.objects.create(
                    empresa=empresa,
                    cuenta_fk=contrapartida,
                    cuenta_text=contrapartida.nombre,
                    tipo='debito',
                    monto=cuenta_data['monto_inicial'],
                    descripcion=f'Apertura cuenta {cuenta.nombre}',
                    transaccion_id=transaccion_id
                )
        
        # Limpiar sesión
        request.session.pop('cuenta_data', None)
        
        messages.success(request, f'Cuenta "{cuenta.nombre}" creada con asientos contables.')
        return redirect('empresa:listar_cuentas_contables')
    
    # Mostrar formulario inicial
    return render(request, 'empresa/crear_cuenta_contable.html', {})

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
