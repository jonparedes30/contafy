"""
Estado de Resultados - Vista simple y NIIF.

Fuente de verdad:
    Esta vista usa los modelos directos (Venta, Compra, Gasto) como fuente
    de cálculo. Para el reporte estructurado según NIIF se prefieren las
    cuentas contables (MovimientoContable) — ver `niif_compliance.estado_resultados_niif`.

Fórmula contable (forma estándar):
    Utilidad bruta      = Ingresos netos − Costo de ventas
    Utilidad operativa  = Utilidad bruta − Gastos operativos
    Utilidad antes de impuestos = Utilidad operativa − Gastos financieros
    Utilidad neta       = Utilidad antes de impuestos − Impuestos

    Donde:
        - Ingresos netos = ventas SIN IVA (monto_neto)
        - Costo de ventas = compras de inventario del período (monto_neto)
        - Gastos operativos = total de Gastos del período
"""
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from empresa.models import Compra, Gasto, Venta
from django.utils import timezone

# Tasas impositivas Ecuador (NIIF + LRTI). Pueden externalizarse a settings.
TASA_PARTICIPACION_TRABAJADORES = Decimal('0.15')  # 15% Participación Trabajadores
TASA_IMPUESTO_RENTA = Decimal('0.25')               # 25% Impuesto a la Renta


def _to_decimal(value):
    return Decimal(str(value or 0))


@login_required
def estado_resultados_simple(request):
    empresa = request.user.empresa

    # ───────────────────────────────────────────────
    # 1. Resolver rango de fechas
    # ───────────────────────────────────────────────
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    try:
        fecha_inicio = (
            datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            if fecha_inicio_str else timezone.localdate().replace(day=1)
        )
        fecha_fin = (
            datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            if fecha_fin_str else timezone.localdate()
        )
    except ValueError:
        fecha_inicio = timezone.localdate().replace(day=1)
        fecha_fin = timezone.localdate()

    rango = {
        'fecha__date__gte': fecha_inicio,
        'fecha__date__lte': fecha_fin,
    }

    # ───────────────────────────────────────────────
    # 2. Ingresos netos (ventas sin IVA)
    # ───────────────────────────────────────────────
    # Usa monto_neto (sin IVA). Si por dato histórico monto_neto = 0,
    # se cae al `monto` total para evitar reportes vacíos en demos legacy.
    ventas_qs = Venta.objects.filter(empresa=empresa, **rango)
    ventas_netas = _to_decimal(ventas_qs.aggregate(t=Sum('monto_neto'))['t'])
    ventas_brutas = _to_decimal(ventas_qs.aggregate(t=Sum('monto'))['t'])
    ingresos_netos = ventas_netas if ventas_netas > 0 else ventas_brutas

    # ───────────────────────────────────────────────
    # 3. Costo de ventas
    # ───────────────────────────────────────────────
    # Aproximación: compras de inventario del período (sin IVA).
    # Para una versión NIIF estricta debería usarse PEPS/FIFO movimiento por
    # movimiento (`ContabilidadService.crear_asientos_venta` ya lo hace al
    # registrar cada venta — ver `estado_resultados_niif` para esa vista).
    compras_qs = Compra.objects.filter(empresa=empresa, **rango)
    costo_ventas_neto = _to_decimal(compras_qs.aggregate(t=Sum('monto_neto'))['t'])
    costo_ventas_bruto = _to_decimal(compras_qs.aggregate(t=Sum('monto'))['t'])
    costo_ventas = costo_ventas_neto if costo_ventas_neto > 0 else costo_ventas_bruto

    # ───────────────────────────────────────────────
    # 4. Gastos operativos
    # ───────────────────────────────────────────────
    gastos_operativos = _to_decimal(
        Gasto.objects.filter(empresa=empresa, **rango)
        .aggregate(t=Sum('monto'))['t']
    )

    # ───────────────────────────────────────────────
    # 5. Cálculo en cascada
    # ───────────────────────────────────────────────
    utilidad_bruta = ingresos_netos - costo_ventas
    utilidad_operativa = utilidad_bruta - gastos_operativos

    # Impuestos: solo aplican si hay utilidad positiva (no se generan
    # créditos fiscales por pérdidas en esta vista simple).
    if utilidad_operativa > 0:
        participacion_trabajadores = utilidad_operativa * TASA_PARTICIPACION_TRABAJADORES
        utilidad_antes_ir = utilidad_operativa - participacion_trabajadores
        impuesto_renta = utilidad_antes_ir * TASA_IMPUESTO_RENTA
    else:
        participacion_trabajadores = Decimal('0')
        utilidad_antes_ir = utilidad_operativa
        impuesto_renta = Decimal('0')

    utilidad_neta = utilidad_antes_ir - impuesto_renta

    # ───────────────────────────────────────────────
    # 6. Cuadre — verificación de consistencia
    # ───────────────────────────────────────────────
    # Suma de componentes debe coincidir con utilidad_neta.
    cuadre_check = ingresos_netos - costo_ventas - gastos_operativos - participacion_trabajadores - impuesto_renta
    cuadra = abs(cuadre_check - utilidad_neta) < Decimal('0.01')

    # ───────────────────────────────────────────────
    # 7. Construir contexto según formato solicitado
    # ───────────────────────────────────────────────
    formato_niif = request.GET.get('niif', 'false') == 'true'

    if formato_niif:
        reporte_niif = {
            'ingresos_ordinarios': {
                'Ventas': float(ingresos_netos),
            },
            'costos_ventas': {
                'Costo de Ventas (compras de inventario)': float(costo_ventas),
            },
            'gastos_operativos': {
                'Gastos Operativos': float(gastos_operativos),
            },
            'impuestos': {
                'Participación Trabajadores (15%)': float(participacion_trabajadores),
                'Impuesto a la Renta (25%)': float(impuesto_renta),
            },
            'totales': {
                'ingresos_ordinarios': float(ingresos_netos),
                'costos_ventas': float(costo_ventas),
                'utilidad_bruta': float(utilidad_bruta),
                'gastos_operativos': float(gastos_operativos),
                'utilidad_operativa': float(utilidad_operativa),
                'participacion_trabajadores': float(participacion_trabajadores),
                'impuesto_renta': float(impuesto_renta),
                'utilidad_neta': float(utilidad_neta),
            },
        }
        context = {
            'reporte_niif': reporte_niif,
            'formato_niif': True,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'cuadra': cuadra,
            'utilidad_neta': float(utilidad_neta),
            'ventas': float(ingresos_netos),
            'costos': float(costo_ventas),
            'gastos': float(gastos_operativos),
            'utilidad_bruta': float(utilidad_bruta),
            'utilidad_operativa': float(utilidad_operativa),
        }
    else:
        context = {
            'ventas': float(ingresos_netos),
            'costos': float(costo_ventas),
            'gastos': float(gastos_operativos),
            'utilidad_bruta': float(utilidad_bruta),
            'utilidad_operativa': float(utilidad_operativa),
            'participacion_trabajadores': float(participacion_trabajadores),
            'impuesto_renta': float(impuesto_renta),
            'utilidad_neta': float(utilidad_neta),
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'formato_niif': False,
            'cuadra': cuadra,
        }

    return render(request, 'empresa/estado_resultado.html', context)
