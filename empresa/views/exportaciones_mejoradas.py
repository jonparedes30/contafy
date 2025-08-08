from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from empresa.models import *
from datetime import datetime, timedelta
import io

@login_required
def exportaciones_comercio(request):
    empresa = request.user.empresa
    
    # Estadísticas para vista previa
    stats = {
        'total_ventas': Venta.objects.filter(empresa=empresa).aggregate(total=Sum('monto'))['total'] or 0,
        'total_gastos': Gasto.objects.filter(empresa=empresa).aggregate(total=Sum('monto'))['total'] or 0,
        'total_productos': Producto.objects.filter(empresa=empresa).count(),
        'utilidad': 0
    }
    stats['utilidad'] = stats['total_ventas'] - stats['total_gastos']
    
    return render(request, 'empresa/exportaciones_comercio.html', {'stats': stats})

@login_required
def exportaciones_manufactura(request):
    empresa = request.user.empresa
    
    # Estadísticas para vista previa
    stats = {
        'total_materias': MateriaPrima.objects.filter(empresa=empresa).count(),
        'total_productos': ProductoManufacturado.objects.filter(empresa=empresa).count(),
        'ordenes_pendientes': OrdenProduccion.objects.filter(empresa=empresa, estado='pendiente').count(),
        'ordenes_proceso': OrdenProduccion.objects.filter(empresa=empresa, estado='en_proceso').count(),
        'ventas_mes': Venta.objects.filter(empresa=empresa, fecha__month=datetime.now().month).aggregate(total=Sum('monto'))['total'] or 0,
        'costos_mes': ConsumoMateriaPrima.objects.filter(empresa=empresa, fecha_consumo__month=datetime.now().month).aggregate(total=Sum('costo_total'))['total'] or 0,
    }
    
    return render(request, 'empresa/exportaciones_manufactura.html', {'stats': stats})

@login_required
def exportar_excel_ventas_manufactura(request):
    from openpyxl import Workbook
    empresa = request.user.empresa
    ventas = Venta.objects.filter(empresa=empresa).select_related('producto')
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas Manufactura"
    
    headers = ['Fecha', 'Producto', 'Cantidad', 'Precio Unitario', 'Total', 'Cliente', 'Tipo Pago']
    ws.append(headers)
    
    for venta in ventas:
        ws.append([
            venta.fecha.strftime('%d/%m/%Y'),
            venta.producto.nombre,
            venta.cantidad,
            float(venta.precio_unitario),
            float(venta.monto),
            venta.cliente_display,
            venta.get_tipo_pago_display()
        ])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="ventas_manufactura_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response

@login_required
def exportar_pdf_comercio_bancario(request):
    empresa = request.user.empresa
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []
    
    # Título principal
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=18, spaceAfter=30, textColor=colors.darkblue)
    elements.append(Paragraph(f"REPORTE FINANCIERO BANCARIO", title_style))
    elements.append(Paragraph(f"{empresa.nombre.upper()}", styles['Heading1']))
    elements.append(Paragraph(f"RUC: {empresa.ruc} | Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Resumen ejecutivo
    elements.append(Paragraph("RESUMEN EJECUTIVO", styles['Heading2']))
    ventas_total = Venta.objects.filter(empresa=empresa).aggregate(total=Sum('monto'))['total'] or 0
    gastos_total = Gasto.objects.filter(empresa=empresa).aggregate(total=Sum('monto'))['total'] or 0
    utilidad = ventas_total - gastos_total
    
    resumen_data = [
        ['Concepto', 'Monto (USD)', 'Porcentaje'],
        ['Ingresos Totales', f"${ventas_total:,.2f}", "100%"],
        ['Gastos Totales', f"${gastos_total:,.2f}", f"{(gastos_total/ventas_total*100) if ventas_total > 0 else 0:.1f}%"],
        ['Utilidad Neta', f"${utilidad:,.2f}", f"{(utilidad/ventas_total*100) if ventas_total > 0 else 0:.1f}%"],
        ['Margen de Utilidad', f"{(utilidad/ventas_total*100) if ventas_total > 0 else 0:.1f}%", ""],
    ]
    
    table = Table(resumen_data, colWidths=[2*inch, 1.5*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Análisis de liquidez
    elements.append(Paragraph("ANÁLISIS DE LIQUIDEZ Y SOLVENCIA", styles['Heading2']))
    productos_count = Producto.objects.filter(empresa=empresa).count()
    try:
        productos = Producto.objects.filter(empresa=empresa)
        inventario_valor = sum(float(p.precio_unitario or 0) * p.stock for p in productos)
    except:
        inventario_valor = 0
    
    liquidez_data = [
        ['Indicador', 'Valor', 'Interpretación'],
        ['Productos en Inventario', f"{productos_count}", "Diversificación de productos"],
        ['Valor del Inventario', f"${inventario_valor:,.2f}", "Activos disponibles"],
        ['Rotación Mensual', f"{ventas_total/12:,.2f}" if ventas_total > 0 else "$0.00", "Promedio mensual de ventas"],
        ['Ratio Gastos/Ingresos', f"{(gastos_total/ventas_total) if ventas_total > 0 else 0:.2f}", "Eficiencia operativa"],
    ]
    
    table2 = Table(liquidez_data, colWidths=[2*inch, 1.5*inch, 2*inch])
    table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table2)
    
    # Proyecciones
    elements.append(PageBreak())
    elements.append(Paragraph("PROYECCIONES FINANCIERAS", styles['Heading2']))
    proyeccion_anual = float(ventas_total) * 1.15  # Proyección 15% crecimiento
    
    elements.append(Paragraph(f"Basado en el desempeño actual, se proyecta un crecimiento del 15% para el próximo período, "
                             f"alcanzando ingresos estimados de ${proyeccion_anual:,.2f}.", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_bancario_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    return response

@login_required
def exportar_pdf_comercio_interno(request):
    empresa = request.user.empresa
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Título simple
    elements.append(Paragraph(f"Reporte Interno - {empresa.nombre}", styles['Title']))
    elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Métricas básicas
    ventas_mes = Venta.objects.filter(empresa=empresa, fecha__month=datetime.now().month).aggregate(total=Sum('monto'))['total'] or 0
    gastos_mes = Gasto.objects.filter(empresa=empresa, fecha__month=datetime.now().month).aggregate(total=Sum('monto'))['total'] or 0
    
    metricas_data = [
        ['Métrica', 'Valor'],
        ['Ventas del Mes', f"${ventas_mes:,.2f}"],
        ['Gastos del Mes', f"${gastos_mes:,.2f}"],
        ['Utilidad del Mes', f"${ventas_mes - gastos_mes:,.2f}"],
        ['Productos Activos', f"{Producto.objects.filter(empresa=empresa).count()}"],
    ]
    
    table = Table(metricas_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_interno_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    return response

@login_required
def exportar_pdf_manufactura_bancario(request):
    empresa = request.user.empresa
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []
    
    # Título principal
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=18, spaceAfter=30, textColor=colors.darkgreen)
    elements.append(Paragraph(f"REPORTE FINANCIERO MANUFACTURERO", title_style))
    elements.append(Paragraph(f"{empresa.nombre.upper()}", styles['Heading1']))
    elements.append(Paragraph(f"RUC: {empresa.ruc} | Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Análisis de costos de producción
    elements.append(Paragraph("ANÁLISIS DE COSTOS DE PRODUCCIÓN", styles['Heading2']))
    
    try:
        materias = MateriaPrima.objects.filter(empresa=empresa)
        materias_valor = sum(float(m.precio_unitario or 0) * float(m.stock_actual or 0) for m in materias)
    except:
        materias_valor = 0
    
    productos_costo = ProductoManufacturado.objects.filter(empresa=empresa).aggregate(
        precio_costo__avg=Avg('precio_costo'), precio_costo__sum=Sum('precio_costo')
    )
    
    costos_data = [
        ['Concepto', 'Valor (USD)', 'Observaciones'],
        ['Inventario Materias Primas', f"${materias_valor:,.2f}", "Activo productivo"],
        ['Costo Promedio Producto', f"${productos_costo['precio_costo__avg'] or 0:.2f}", "Eficiencia de producción"],
        ['Productos en Catálogo', f"{ProductoManufacturado.objects.filter(empresa=empresa).count()}", "Diversificación"],
        ['Órdenes Completadas', f"{OrdenProduccion.objects.filter(empresa=empresa, estado='completada').count()}", "Capacidad productiva"],
    ]
    
    table = Table(costos_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Eficiencia operativa
    elements.append(Paragraph("INDICADORES DE EFICIENCIA", styles['Heading2']))
    ordenes_pendientes = OrdenProduccion.objects.filter(empresa=empresa, estado='pendiente').count()
    ordenes_proceso = OrdenProduccion.objects.filter(empresa=empresa, estado='en_proceso').count()
    
    eficiencia_data = [
        ['Indicador', 'Valor', 'Estado'],
        ['Órdenes Pendientes', f"{ordenes_pendientes}", "En cola de producción"],
        ['Órdenes en Proceso', f"{ordenes_proceso}", "Producción activa"],
        ['Materias con Stock Bajo', f"{MateriaPrima.objects.filter(empresa=empresa, stock_actual__lte=F('stock_minimo')).count()}", "Requiere reabastecimiento"],
        ['Tiempo Promedio Producción', "Calculado por orden", "Optimización continua"],
    ]
    
    table2 = Table(eficiencia_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
    table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table2)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_manufactura_bancario_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    return response

@login_required
def exportar_pdf_manufactura_interno(request):
    empresa = request.user.empresa
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Título simple
    elements.append(Paragraph(f"Reporte Operativo - {empresa.nombre}", styles['Title']))
    elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Métricas operativas
    metricas_data = [
        ['Métrica', 'Valor'],
        ['Materias Primas', f"{MateriaPrima.objects.filter(empresa=empresa).count()}"],
        ['Productos Activos', f"{ProductoManufacturado.objects.filter(empresa=empresa, activo=True).count()}"],
        ['Órdenes Pendientes', f"{OrdenProduccion.objects.filter(empresa=empresa, estado='pendiente').count()}"],
        ['Órdenes en Proceso', f"{OrdenProduccion.objects.filter(empresa=empresa, estado='en_proceso').count()}"],
        ['Órdenes Completadas', f"{OrdenProduccion.objects.filter(empresa=empresa, estado='completada').count()}"],
    ]
    
    table = Table(metricas_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_operativo_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    return response