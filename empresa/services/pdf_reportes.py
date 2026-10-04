"""Reportes PDF con la identidad visual de Contafy (ReportLab).

Las cifras salen del libro contable (empresa.services.saldos) para que el PDF
coincida con el Resumen, el Estado de Resultados y el Balance de la app.
Helvetica no tiene emojis: no usarlos en los textos de los PDF.
"""
import io
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from empresa.services.saldos import estado_resultados_periodo

# Paleta de marca (docs/DESIGN_SYSTEM.md)
VERDE = colors.HexColor('#10b981')
VERDE_OSCURO = colors.HexColor('#047857')
TINTA = colors.HexColor('#0f172a')
GRIS = colors.HexColor('#64748b')
GRIS_CLARO = colors.HexColor('#f1f5f9')
BORDE = colors.HexColor('#e2e8f0')
ROJO = colors.HexColor('#dc2626')

MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def _estilos():
    base = getSampleStyleSheet()
    return {
        'titulo': ParagraphStyle('t', parent=base['Title'], fontName='Helvetica-Bold', fontSize=18,
                                 textColor=colors.white, alignment=0, spaceAfter=2, leading=22),
        'subtitulo': ParagraphStyle('st', parent=base['Normal'], fontSize=9.5, textColor=colors.white, leading=13),
        'h2': ParagraphStyle('h2', parent=base['Heading2'], fontName='Helvetica-Bold', fontSize=12,
                             textColor=TINTA, spaceBefore=14, spaceAfter=6),
        'normal': ParagraphStyle('n', parent=base['Normal'], fontSize=9, textColor=TINTA, leading=12),
        'nota': ParagraphStyle('nota', parent=base['Normal'], fontSize=8, textColor=GRIS, leading=11),
        'derecha': ParagraphStyle('d', parent=base['Normal'], fontSize=9, alignment=TA_RIGHT),
    }


def _dinero(valor):
    valor = Decimal(valor or 0)
    signo = '-' if valor < 0 else ''
    return f"{signo}${abs(valor):,.2f}"


def _variacion(actual, anterior):
    actual, anterior = Decimal(actual or 0), Decimal(anterior or 0)
    if anterior == 0:
        return '—'
    cambio = (actual - anterior) / abs(anterior) * 100
    return f"{'+' if cambio >= 0 else ''}{cambio:.1f}%"


def _tabla(filas, anchos, numericas_desde=1, resaltar_filas=()):
    tabla = Table(filas, colWidths=anchos, repeatRows=1)
    estilo = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), GRIS),
        ('LINEBELOW', (0, 0), (-1, 0), 1, BORDE),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, BORDE),
        ('ALIGN', (numericas_desde, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for fila in resaltar_filas:
        estilo += [('FONTNAME', (0, fila), (-1, fila), 'Helvetica-Bold'),
                   ('BACKGROUND', (0, fila), (-1, fila), GRIS_CLARO)]
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _encabezado(empresa, titulo, periodo, estilos, ancho):
    texto = [
        Paragraph(titulo, estilos['titulo']),
        Paragraph(f"{empresa.nombre} &nbsp;·&nbsp; RUC {empresa.ruc or 's/n'}", estilos['subtitulo']),
        Paragraph(f"Período: {periodo} &nbsp;·&nbsp; Generado el "
                  f"{timezone.localtime().strftime('%d/%m/%Y %H:%M')}", estilos['subtitulo']),
    ]
    banda = Table([[texto]], colWidths=[ancho])
    banda.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), VERDE_OSCURO),
        ('LEFTPADDING', (0, 0), (-1, -1), 14), ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    return banda


def _pie(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(GRIS)
    canvas.drawString(doc.leftMargin, 1.2 * cm, 'Contafy · Reporte interno — uso exclusivo de la empresa')
    canvas.drawRightString(A4[0] - doc.rightMargin, 1.2 * cm, f'Página {doc.page}')
    canvas.restoreState()


def reporte_interno_pdf(empresa, hoy=None):
    """Reporte interno del mes en curso comparado con el mes anterior. Devuelve bytes del PDF."""
    from empresa.models import CuentaPorCobrar, Producto, Venta

    hoy = hoy or timezone.localdate()
    inicio_mes = hoy.replace(day=1)
    fin_mes_anterior = inicio_mes - timedelta(days=1)
    inicio_mes_anterior = fin_mes_anterior.replace(day=1)
    # Comparar el mismo tramo de días para que la variación sea justa.
    corte_anterior = min(fin_mes_anterior, inicio_mes_anterior + (hoy - inicio_mes))

    actual = estado_resultados_periodo(empresa, inicio_mes, hoy)
    anterior = estado_resultados_periodo(empresa, inicio_mes_anterior, corte_anterior)

    estilos = _estilos()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.5 * cm, bottomMargin=2 * cm,
                            title=f'Reporte interno {empresa.nombre}')
    ancho = A4[0] - doc.leftMargin - doc.rightMargin
    periodo = f"1 al {hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"
    elementos = [_encabezado(empresa, 'Reporte Interno', periodo, estilos, ancho), Spacer(1, 10)]

    # 1. Resultados del mes
    elementos.append(Paragraph('Resultados del mes', estilos['h2']))
    etiqueta_anterior = f"{MESES[inicio_mes_anterior.month - 1].capitalize()} (1-{corte_anterior.day})"
    filas = [['Concepto', f"{MESES[hoy.month - 1].capitalize()} {hoy.year}", etiqueta_anterior, 'Variación']]
    for clave, nombre in [('ventas', 'Ventas netas (sin IVA)'), ('costo_ventas', 'Costo de ventas'),
                          ('utilidad_bruta', 'Utilidad bruta'), ('gastos', 'Gastos operativos'),
                          ('utilidad_neta', 'Utilidad neta')]:
        filas.append([nombre, _dinero(actual[clave]), _dinero(anterior[clave]),
                      _variacion(actual[clave], anterior[clave])])
    filas.append(['Margen neto', f"{actual['margen_neto']:.1f}%", f"{anterior['margen_neto']:.1f}%", ''])
    tabla = _tabla(filas, [6.2 * cm, 3.6 * cm, 3.6 * cm, 2.6 * cm], resaltar_filas=(3, 5))
    if actual['utilidad_neta'] < 0:
        tabla.setStyle(TableStyle([('TEXTCOLOR', (1, 5), (1, 5), ROJO)]))
    elementos.append(tabla)
    if not actual['ventas']:
        elementos.append(Spacer(1, 4))
        elementos.append(Paragraph('Aún no hay ventas registradas este mes.', estilos['nota']))

    # 2. Productos más vendidos del mes
    top = (Venta.objects.filter(empresa=empresa, fecha__date__gte=inicio_mes, fecha__date__lte=hoy)
           .values('producto__nombre')
           .annotate(unidades=Sum('cantidad'), total=Sum('monto_neto'))
           .order_by('-total')[:5])
    elementos.append(Paragraph('Productos más vendidos', estilos['h2']))
    if top:
        filas = [['Producto', 'Unidades', 'Ventas netas']]
        filas += [[t['producto__nombre'], f"{t['unidades']:,}", _dinero(t['total'])] for t in top]
        elementos.append(_tabla(filas, [9.8 * cm, 2.8 * cm, 3.4 * cm]))
    else:
        elementos.append(Paragraph('Sin ventas en el período.', estilos['nota']))

    # 3. Inventario por reponer
    bajos = (Producto.objects.filter(empresa=empresa, es_servicio=False, stock__lte=F('stock_minimo'))
             .order_by('stock')[:10])
    elementos.append(Paragraph('Inventario por reponer', estilos['h2']))
    if bajos:
        filas = [['Producto', 'Stock', 'Mínimo']]
        filas += [[p.nombre, f"{p.stock:,}", f"{p.stock_minimo:,}"] for p in bajos]
        elementos.append(_tabla(filas, [9.8 * cm, 2.8 * cm, 3.4 * cm]))
    else:
        elementos.append(Paragraph('Todos los productos están sobre su stock mínimo.', estilos['nota']))

    # 4. Cuentas por cobrar
    pendientes = CuentaPorCobrar.objects.filter(empresa=empresa, monto_pendiente__gt=0)
    total_cxc = pendientes.aggregate(s=Sum('monto_pendiente'))['s'] or 0
    vencidas = pendientes.filter(fecha_vencimiento__lt=hoy)
    total_vencido = vencidas.aggregate(s=Sum('monto_pendiente'))['s'] or 0
    elementos.append(Paragraph('Cuentas por cobrar', estilos['h2']))
    filas = [['Concepto', 'Cuentas', 'Monto'],
             ['Pendientes de cobro', f"{pendientes.count():,}", _dinero(total_cxc)],
             ['De ellas, vencidas', f"{vencidas.count():,}", _dinero(total_vencido)]]
    elementos.append(_tabla(filas, [9.8 * cm, 2.8 * cm, 3.4 * cm]))

    elementos.append(Spacer(1, 14))
    elementos.append(Paragraph(
        'Las cifras provienen de los asientos contables de Contafy. La utilidad descuenta el costo de '
        'la mercadería vendida (no el total de compras) y excluye el IVA.', estilos['nota']))

    doc.build(elementos, onFirstPage=_pie, onLaterPages=_pie)
    return buffer.getvalue()
