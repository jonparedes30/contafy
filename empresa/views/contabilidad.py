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
    empresa = request.user.empresa
    
    # Obtener filtros de fecha
    from empresa.services.filtros_service import FiltrosFechaService
    fecha_inicio, fecha_fin = FiltrosFechaService.obtener_rango_fechas(request)
    
    # Obtener datos filtrados por fecha
    ventas = FiltrosFechaService.obtener_movimientos_contables_por_periodo(
        empresa, 'Ventas', 'credito', fecha_inicio, fecha_fin
    )
    # COSTO DE VENTAS - Usar cuenta contable (ya corregida)
    costos = FiltrosFechaService.obtener_movimientos_contables_por_periodo(
        empresa, 'Costo de Ventas', 'debito', fecha_inicio, fecha_fin
    )
    gastos = FiltrosFechaService.obtener_movimientos_contables_por_periodo(
        empresa, 'Gastos', 'debito', fecha_inicio, fecha_fin
    )
    
    utilidad_bruta = ventas - costos
    utilidad_neta = utilidad_bruta - gastos  # CORREGIDO: Ventas - Costos - Gastos
    
    contexto = {
        'ventas': float(ventas),
        'costos': float(costos),
        'gastos': float(gastos),
        'utilidad_bruta': float(utilidad_bruta),
        'utilidad_operativa': float(utilidad_neta),  # CORREGIDO: Utilidad después de gastos
        'utilidad_neta': float(utilidad_neta),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'empresa/estado_resultado.html', contexto)

# ======================
# FLUJO DE CAJA ESTIMADO
# ======================
@login_required
def flujo_caja(request):
    empresa = request.user.empresa
    
    # Análisis completo con DCF y proyecciones
    from empresa.services.flujo_caja_dcf_service import FlujoCajaDCFService
    analisis_completo = FlujoCajaDCFService.calcular_flujo_completo(empresa)
    
    # Flujo histórico para compatibilidad con template existente
    hoy = datetime.today()
    año_actual = hoy.year
    meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    
    # Buscar la cuenta de Caja/Banco
    try:
        cuenta_caja = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Caja/Banco')
    except CuentaContable.DoesNotExist:
        cuenta_caja = None

    flujo = []
    total_entradas = 0.0
    total_salidas = 0.0
    meses_positivos = 0
    acumulado = 0.0
    
    for idx, mes_nombre in enumerate(meses, start=1):
        # Entradas de efectivo: Ventas + Otros ingresos
        try:
            cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
            entradas_ventas = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_ventas,
                tipo='credito',
                fecha__year=año_actual,
                fecha__month=idx
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            entradas_ventas = 0
        
        # Salidas de efectivo: Gastos + Costos de Ventas + Compras
        try:
            cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
            salidas_gastos = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_gastos,
                tipo='debito',
                fecha__year=año_actual,
                fecha__month=idx
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            salidas_gastos = 0
        
        # INCLUIR COSTOS DE VENTAS EN FLUJO DE CAJA
        try:
            cuenta_costos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Costo de Ventas')
            salidas_costos = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_costos,
                tipo='debito',
                fecha__year=año_actual,
                fecha__month=idx
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            salidas_costos = 0
        
        try:
            cuenta_inventario = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Inventario')
            salidas_compras = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_inventario,
                tipo='debito',
                fecha__year=año_actual,
                fecha__month=idx
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            salidas_compras = 0
        
        entradas = float(entradas_ventas)
        salidas = float(salidas_gastos + salidas_costos + salidas_compras)
        
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
        # Datos tradicionales
        'flujo': flujo,
        'labels': meses,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
        'flujo_neto_total': flujo_neto_total,
        'meses_positivos': meses_positivos,
        'total_meses': total_meses,
        # Análisis avanzado con DCF
        'analisis_completo': analisis_completo,
    })

@login_required
def balance_general(request):
    empresa = request.user.empresa
    
    # Obtener filtros de fecha
    from empresa.services.filtros_service import FiltrosFechaService
    fecha_inicio, fecha_fin = FiltrosFechaService.obtener_rango_fechas(request)

    # Obtener todas las cuentas contables de la empresa
    cuentas = CuentaContable.objects.filter(empresa=empresa)
    
    # Obtener todos los movimientos filtrados por fecha
    movimientos = MovimientoContable.objects.filter(
        empresa=empresa,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).values(
        'cuenta_fk', 'tipo'
    ).annotate(
        total=Sum('monto')
    )
    
    # Crear diccionario para acceso rápido
    movimientos_dict = {}
    for mov in movimientos:
        key = (mov['cuenta_fk'], mov['tipo'])
        movimientos_dict[key] = mov['total']
    
    activos = []
    pasivos = []
    capital = []
    total_activos = 0
    total_pasivos = 0
    total_capital = 0

    for cuenta in cuentas:
        # Usar el método valor del modelo que ya tiene la lógica correcta
        try:
            saldo = cuenta.valor
        except Exception:
            # Fallback: calcular manualmente si hay error
            debitos = movimientos_dict.get((cuenta.id, 'debito'), 0)
            creditos = movimientos_dict.get((cuenta.id, 'credito'), 0)
            
            if cuenta.tipo in ['activo', 'gasto']:
                saldo = debitos - creditos
            else:  # pasivo, capital, ingreso
                saldo = creditos - debitos

        cuenta_dict = {
            'cuenta_fk__nombre': cuenta.nombre,
            'valor': saldo
        }
        
        # Solo incluir cuentas con saldo diferente de cero
        if abs(saldo) > 0.01:  # Evitar errores de redondeo
            if cuenta.tipo == 'activo':
                activos.append(cuenta_dict)
                total_activos += saldo
            elif cuenta.tipo == 'pasivo':
                pasivos.append(cuenta_dict)
                total_pasivos += saldo
            elif cuenta.tipo == 'capital':
                capital.append(cuenta_dict)
                total_capital += saldo

    # Cálculo de patrimonio (Activos - Pasivos)
    total_activos_float = float(total_activos or 0.0)
    total_pasivos_float = float(total_pasivos or 0.0)
    total_patrimonio = total_activos_float - total_pasivos_float

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
    }
    return render(request, 'empresa/balance_general.html', contexto)

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
