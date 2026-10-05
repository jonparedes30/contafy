from django.shortcuts import render
from datetime import datetime
from decimal import Decimal
import logging
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from empresa.models import Venta, Compra, Gasto, CuentaContable, MovimientoContable
from empresa.views.resumen import obtener_totales_contables
from django.utils import timezone

# ======================
# ESTADO DE RESULTADOS
# ======================

logger = logging.getLogger(__name__)

@login_required
def estado_resultados(request):
    return render(request, 'empresa/estado_resultado.html', {
        'ventas': 1500.00,
        'costos': 800.00,
        'gastos': 400.00,
        'utilidad_bruta': 700.00,
        'utilidad_operativa': 300.00,
        'utilidad_neta': 300.00,
        'fecha_inicio': timezone.localdate().replace(day=1),
        'fecha_fin': timezone.localdate(),
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
                fecha_inicio = timezone.localdate().replace(day=1)
                fecha_fin = timezone.localdate()
        else:
            fecha_inicio = timezone.localdate().replace(day=1)
            fecha_fin = timezone.localdate()
        
        # Obtener cuentas contables
        cuentas = CuentaContable.objects.filter(empresa=empresa)
        
        activos = []
        pasivos = []
        capital = []
        total_activos = 0
        total_pasivos = 0
        total_capital = 0
        resultado_ejercicio = 0
        
        # El capital aportado ya está en el libro (asiento Caja/Capital, migración 0032):
        # no se suma el modelo Capital por fuera para no contarlo dos veces.

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

                # Ingresos y gastos no cerrados = resultado del ejercicio (parte del patrimonio).
                # 'Ventas' es ingreso aunque datos antiguos la marcaran como capital.
                if cuenta.tipo == 'ingreso' or cuenta.nombre.strip().lower() == 'ventas':
                    resultado_ejercicio += saldo
                    continue
                if cuenta.tipo == 'gasto':
                    resultado_ejercicio -= saldo
                    continue

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
                logger.exception('Balance general: no se pudo calcular la cuenta %s', cuenta.nombre)
                continue

        total_activos_float = float(total_activos or 0.0)
        total_pasivos_float = float(total_pasivos or 0.0)
        resultado_ejercicio = float(resultado_ejercicio or 0.0)
        if abs(resultado_ejercicio) > 0.01:
            capital.append({'cuenta_fk__nombre': 'Resultado del ejercicio', 'valor': resultado_ejercicio})
        # Patrimonio real (no "activos - pasivos", que cuadraría siempre por construcción).
        total_patrimonio = float(total_capital or 0.0) + resultado_ejercicio
        diferencia_cuadre = round(total_activos_float - total_pasivos_float - total_patrimonio, 2)
        cuadra = abs(diferencia_cuadre) < 0.01
        if not cuadra:
            logger.warning('Balance de %s no cuadra: diferencia %s', empresa.nombre, diferencia_cuadre)
        
        # Verificar si se solicita formato NIIF
        formato_niif = request.GET.get('niif', 'false') == 'true'

        if formato_niif:
            # Clasificación NIIF: corriente vs no corriente por nombre de cuenta
            # (Heurística — futuro: agregar campo `clasificacion_niif` al modelo CuentaContable)
            NOMBRES_ACTIVO_CORRIENTE = {
                'caja', 'bancos', 'banco', 'cuentas por cobrar', 'inventario',
                'inventarios', 'iva crédito fiscal', 'iva credito fiscal',
                'caja/banco', 'caja (capital)', 'efectivo', 'inversiones temporales',
                'inventario - materia prima', 'inventario - producto terminado',
                'producción en proceso', 'produccion en proceso', 'anticipos',
            }
            NOMBRES_PASIVO_CORRIENTE = {
                'cuentas por pagar', 'iva por pagar', 'sueldos por pagar',
                'impuestos por pagar', 'préstamos a corto plazo', 'prestamos a corto plazo',
                'obligaciones a corto plazo', 'acreedores',
            }

            def es_activo_corriente(nombre):
                n = nombre.lower().strip()
                # match exacto en whitelist, o starts-with común
                return (n in NOMBRES_ACTIVO_CORRIENTE
                        or n.startswith('caja') or n.startswith('banco')
                        or n.startswith('cuentas por cobrar')
                        or n.startswith('inventario') or n.startswith('iva'))

            def es_pasivo_corriente(nombre):
                n = nombre.lower().strip()
                return (n in NOMBRES_PASIVO_CORRIENTE
                        or n.startswith('cuentas por pagar')
                        or 'iva por pagar' in n
                        or 'corto plazo' in n)

            reporte_niif = {
                'activos_corrientes': {},
                'activos_no_corrientes': {},
                'pasivos_corrientes': {},
                'pasivos_no_corrientes': {},
                'patrimonio': {},
                'totales': {
                    'activos_corrientes': 0.0,
                    'activos_no_corrientes': 0.0,
                    'total_activos': total_activos_float,
                    'pasivos_corrientes': 0.0,
                    'pasivos_no_corrientes': 0.0,
                    'total_pasivos': total_pasivos_float,
                    'total_patrimonio': total_patrimonio,
                    'resultado_ejercicio': resultado_ejercicio,
                    'cuadra': cuadra,
                    'diferencia_cuadre': diferencia_cuadre,
                    # Suma pre-calculada en backend (evita perdida de precisión con |add: en template)
                    'total_pasivos_y_patrimonio': total_pasivos_float + total_patrimonio,
                    # Diferencia para detectar descuadres (>1 centavo)
                    'diferencia_cuadre': abs(total_activos_float - (total_pasivos_float + total_patrimonio)),
                    'cuadra': abs(total_activos_float - (total_pasivos_float + total_patrimonio)) < 0.01,
                }
            }

            # Clasificar activos según corriente/no corriente
            for activo in activos:
                nombre = activo['cuenta_fk__nombre']
                valor = float(activo['valor'])
                if es_activo_corriente(nombre):
                    reporte_niif['activos_corrientes'][nombre] = valor
                    reporte_niif['totales']['activos_corrientes'] += valor
                else:
                    reporte_niif['activos_no_corrientes'][nombre] = valor
                    reporte_niif['totales']['activos_no_corrientes'] += valor

            # Clasificar pasivos
            for pasivo in pasivos:
                nombre = pasivo['cuenta_fk__nombre']
                valor = float(pasivo['valor'])
                if es_pasivo_corriente(nombre):
                    reporte_niif['pasivos_corrientes'][nombre] = valor
                    reporte_niif['totales']['pasivos_corrientes'] += valor
                else:
                    reporte_niif['pasivos_no_corrientes'][nombre] = valor
                    reporte_niif['totales']['pasivos_no_corrientes'] += valor

            # Patrimonio
            for cap in capital:
                reporte_niif['patrimonio'][cap['cuenta_fk__nombre']] = float(cap['valor'])

            contexto = {
                'reporte_niif': reporte_niif,
                'formato_niif': True,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'total_activos': total_activos_float,
                'total_pasivos': total_pasivos_float,
                'total_patrimonio': total_patrimonio,
                'resultado_ejercicio': resultado_ejercicio,
                'cuadra': cuadra,
                'diferencia_cuadre': diferencia_cuadre,
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
                'resultado_ejercicio': resultado_ejercicio,
                'cuadra': cuadra,
                'diferencia_cuadre': diferencia_cuadre,
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
            'fecha_inicio': timezone.localdate().replace(day=1),
            'fecha_fin': timezone.localdate(),
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
    
    # Un débito AUMENTA activos (comprar mercadería nunca debe bloquearse) y
    # DISMINUYE el capital: solo ahí puede dejar la cuenta en negativo.
    if cuenta_debito.tipo == 'capital' and (Decimal(saldo_debito) - Decimal(monto)) < 0:
        raise ValueError(
            f"El movimiento dejaría la cuenta '{cuenta_debito.nombre}' en negativo "
            f"(saldo disponible: ${Decimal(saldo_debito):,.2f})"
        )
    
    # Registrar movimientos débito + crédito agrupados en una sola transacción
    # (garantiza que compartan el mismo transaccion_id - partida doble correcta)
    with MovimientoContable.agrupar_transaccion(descripcion):
        MovimientoContable.objects.create(
            empresa=empresa,
            cuenta_fk=cuenta_debito,
            tipo='debito',
            monto=monto,
            descripcion=descripcion
        )
        MovimientoContable.objects.create(
            empresa=empresa,
            cuenta_fk=cuenta_credito,
            tipo='credito',
            monto=monto,
            descripcion=descripcion
        )
