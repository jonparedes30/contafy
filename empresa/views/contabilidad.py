from django.shortcuts import render
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from empresa.models import Venta, Compra, Gasto, CuentaContable, MovimientoContable
from empresa.views.resumen import obtener_totales_contables

# ======================
# ESTADO DE RESULTADOS
# ======================
@login_required
def estado_resultados(request):
    return render(request, 'empresa/estado_resultado.html', {
        'ventas': 1500.00,
        'costos': 800.00,
        'gastos': 400.00,
        'utilidad_bruta': 700.00,
        'utilidad_operativa': 300.00,
        'utilidad_neta': 300.00,
        'fecha_inicio': datetime.now().replace(day=1).date(),
        'fecha_fin': datetime.now().date(),
        'formato_niif': False,
    })

# ======================
# FLUJO DE CAJA ESTIMADO
# ======================
@login_required
def flujo_caja(request):
    try:
        empresa = request.user.empresa
        if not empresa:
            return render(request, 'empresa/flujo_caja.html', {
                'error': 'No tienes una empresa asociada',
                'flujo': [], 'labels': [],
                'total_entradas': 0, 'total_salidas': 0, 'flujo_neto_total': 0
            })
        
        # Flujo histórico usando datos directos (sin duplicados)
        hoy = datetime.today()
        año_actual = hoy.year
        meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

        flujo = []
        total_entradas = 0.0
        total_salidas = 0.0
        meses_positivos = 0
        acumulado = 0.0
        
        for idx, mes_nombre in enumerate(meses, start=1):
            # ENTRADAS: Usar datos directos de Ventas (evita duplicados de movimientos contables)
            entradas_ventas = Venta.objects.filter(
                empresa=empresa,
                fecha__year=año_actual,
                fecha__month=idx,
                tipo_pago='contado'  # Solo ventas de contado generan flujo inmediato
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            # SALIDAS: Usar datos directos de Gastos y Compras
            salidas_gastos = Gasto.objects.filter(
                empresa=empresa,
                fecha__year=año_actual,
                fecha__month=idx,
                tipo_pago='contado'  # Solo gastos de contado afectan flujo inmediato
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            # Compras de contado (afectan flujo de caja)
            salidas_compras = Compra.objects.filter(
                empresa=empresa,
                fecha__year=año_actual,
                fecha__month=idx,
                tipo_pago='contado'
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            entradas = float(entradas_ventas)
            salidas = float(salidas_gastos + salidas_compras)
            
            neto = entradas - salidas
            acumulado += neto
            
            # Contar meses positivos
            if neto > 0:
                meses_positivos += 1
            
            total_entradas += entradas
            total_salidas += salidas
            
            flujo.append({
                'mes':       mes_nombre,
                'entrada':   entradas,
                'salida':    salidas,
                'neto':      neto,
                'acumulado': acumulado,
            })

        flujo_neto_total = total_entradas - total_salidas
        total_meses = len(meses)

        return render(request, 'empresa/flujo_caja.html', {
            'flujo': flujo,
            'labels': meses,
            'total_entradas': total_entradas,
            'total_salidas': total_salidas,
            'flujo_neto_total': flujo_neto_total,
            'meses_positivos': meses_positivos,
            'total_meses': total_meses,
            'metodo': 'directo',  # Indicar que usa método directo
        })
        
    except Exception as e:
        return render(request, 'empresa/flujo_caja.html', {
            'error': f'Error generando flujo de caja: {str(e)}',
            'flujo': [],
            'labels': ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],
            'total_entradas': 0,
            'total_salidas': 0,
            'flujo_neto_total': 0,
            'meses_positivos': 0,
            'total_meses': 12,
        })

@login_required
def balance_general(request):
    try:
        empresa = request.user.empresa
        if not empresa:
            return render(request, 'empresa/balance_general.html', {
                'error': 'No tienes una empresa asociada',
                'activos': [], 'pasivos': [], 'capital': [],
                'total_activos': 0, 'total_pasivos': 0, 'total_capital': 0, 'total_patrimonio': 0
            })
        
        # Obtener fechas del request o usar valores por defecto
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        
        if fecha_inicio_str and fecha_fin_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = datetime.now().replace(day=1).date()
                fecha_fin = datetime.now().date()
        else:
            fecha_inicio = datetime.now().replace(day=1).date()
            fecha_fin = datetime.now().date()
        
        # Obtener cuentas contables
        cuentas = CuentaContable.objects.filter(empresa=empresa)
        
        activos = []
        pasivos = []
        capital = []
        total_activos = 0
        total_pasivos = 0
        total_capital = 0

        for cuenta in cuentas:
            try:
                # Calcular saldo de la cuenta
                debitos = MovimientoContable.objects.filter(
                    empresa=empresa,
                    cuenta_fk=cuenta,
                    tipo='debito',
                    fecha__date__lte=fecha_fin
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                creditos = MovimientoContable.objects.filter(
                    empresa=empresa,
                    cuenta_fk=cuenta,
                    tipo='credito',
                    fecha__date__lte=fecha_fin
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                if cuenta.tipo in ['activo', 'gasto']:
                    saldo = debitos - creditos
                else:
                    saldo = creditos - debitos

                cuenta_dict = {
                    'cuenta_fk__nombre': cuenta.nombre,
                    'valor': saldo
                }
                
                if abs(saldo) > 0.01:
                    if cuenta.tipo == 'activo':
                        activos.append(cuenta_dict)
                        total_activos += saldo
                    elif cuenta.tipo == 'pasivo':
                        pasivos.append(cuenta_dict)
                        total_pasivos += saldo
                    elif cuenta.tipo == 'capital':
                        capital.append(cuenta_dict)
                        total_capital += saldo
            except Exception:
                continue

        total_activos_float = float(total_activos or 0.0)
        total_pasivos_float = float(total_pasivos or 0.0)
        total_patrimonio = total_activos_float - total_pasivos_float
        
        # Verificar si se solicita formato NIIF
        formato_niif = request.GET.get('niif', 'false') == 'true'
        
        if formato_niif:
            # Estructurar datos según NIIF para Estado de Situación Financiera
            reporte_niif = {
                'activos_corrientes': {},
                'activos_no_corrientes': {},
                'pasivos_corrientes': {},
                'pasivos_no_corrientes': {},
                'patrimonio': {},
                'totales': {
                    'activos_corrientes': 0,
                    'activos_no_corrientes': 0,
                    'total_activos': total_activos_float,
                    'pasivos_corrientes': 0,
                    'pasivos_no_corrientes': 0,
                    'total_pasivos': total_pasivos_float,
                    'total_patrimonio': total_patrimonio,
                }
            }
            
            # Clasificar activos (por simplicidad, todos como corrientes)
            for activo in activos:
                reporte_niif['activos_corrientes'][activo['cuenta_fk__nombre']] = activo['valor']
                reporte_niif['totales']['activos_corrientes'] += activo['valor']
            
            # Clasificar pasivos (por simplicidad, todos como corrientes)
            for pasivo in pasivos:
                reporte_niif['pasivos_corrientes'][pasivo['cuenta_fk__nombre']] = pasivo['valor']
                reporte_niif['totales']['pasivos_corrientes'] += pasivo['valor']
            
            # Clasificar patrimonio
            for cap in capital:
                reporte_niif['patrimonio'][cap['cuenta_fk__nombre']] = cap['valor']
            
            contexto = {
                'reporte_niif': reporte_niif,
                'formato_niif': True,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
            }
        else:
            contexto = {
                'activos': activos,
                'pasivos': pasivos,
                'capital': capital,
                'total_activos': total_activos_float,
                'total_pasivos': total_pasivos_float,
                'total_capital': float(total_capital or 0.0),
                'total_patrimonio': total_patrimonio,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'formato_niif': False,
            }
        
        return render(request, 'empresa/balance_general.html', contexto)
        
    except Exception as e:
        return render(request, 'empresa/balance_general.html', {
            'error': f'Error generando balance: {str(e)}',
            'activos': [],
            'pasivos': [],
            'capital': [],
            'total_activos': 0,
            'total_pasivos': 0,
            'total_capital': 0,
            'total_patrimonio': 0,
            'fecha_inicio': datetime.now().replace(day=1).date(),
            'fecha_fin': datetime.now().date(),
            'formato_niif': False,
        })

# ======================
# REGISTRO DE MOVIMIENTOS
# ======================
def registrar_movimiento_contable(
    empresa,
    cuenta_debito_nombre,
    cuenta_credito_nombre,
    monto,
    descripcion,
    tipo_cuenta_debito='activo',
    tipo_cuenta_credito='pasivo',
):
    # Determinar tipo correcto para cuentas especiales
    if cuenta_debito_nombre.strip().lower() in ['gastos', 'ventas', 'costo de ventas']:
        tipo_cuenta_debito = 'gasto' if 'costo' in cuenta_debito_nombre.lower() else 'capital'
    if cuenta_credito_nombre.strip().lower() in ['gastos', 'ventas', 'costo de ventas']:
        tipo_cuenta_credito = 'gasto' if 'costo' in cuenta_credito_nombre.lower() else 'capital'
    # Obtener o crear la cuenta de débito
    cuenta_debito, _ = CuentaContable.objects.get_or_create(
        empresa=empresa,
        nombre__iexact=cuenta_debito_nombre,
        defaults={'nombre': cuenta_debito_nombre, 'tipo': tipo_cuenta_debito}
    )
    # Obtener o crear la cuenta de crédito
    cuenta_credito, _ = CuentaContable.objects.get_or_create(
        empresa=empresa,
        nombre__iexact=cuenta_credito_nombre,
        defaults={'nombre': cuenta_credito_nombre, 'tipo': tipo_cuenta_credito}
    )
    
    # Calcular saldo actual usando agregación optimizada
    if cuenta_debito.tipo == 'activo':
        saldo_debito = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_debito,
            tipo='debito'
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        saldo_debito -= MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_debito,
            tipo='credito'
        ).aggregate(total=Sum('monto'))['total'] or 0
    else:  # pasivo, capital
        saldo_debito = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_debito,
            tipo='credito'
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        saldo_debito -= MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_debito,
            tipo='debito'
        ).aggregate(total=Sum('monto'))['total'] or 0
    
    # Validar que el movimiento no genere saldo negativo en activos o capital
    if cuenta_debito.tipo in ['activo', 'capital'] and (saldo_debito + monto) < 0:
        raise ValueError(f"El movimiento generaría un saldo negativo en la cuenta '{cuenta_debito.nombre}' ({cuenta_debito.tipo})")
    
    # Registrar movimiento débito
    MovimientoContable.objects.create(
        empresa=empresa,
        cuenta_fk=cuenta_debito,
        tipo='debito',
        monto=monto,
        descripcion=descripcion
    )
    # Registrar movimiento crédito
    MovimientoContable.objects.create(
        empresa=empresa,
        cuenta_fk=cuenta_credito,
        tipo='credito',
        monto=monto,
        descripcion=descripcion
    )
