# empresa/views/ai_reports.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Avg, Count
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF

from empresa.models import Venta, Gasto, Producto, Compra, CuentaContable, MovimientoContable
from empresa.services.ai_agent_service import ContafyAIAgent

@login_required
def generar_reporte_ia_pdf(request):
    """Genera un reporte PDF completo usando análisis de IA"""
    empresa = request.user.empresa
    
    # Obtener análisis de IA
    ai_agent = ContafyAIAgent()
    analisis_ia = ai_agent.analizar_empresa(empresa)
    datos_empresa = ai_agent.obtener_datos_empresa(empresa)
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    
    # Estilos profesionales mejorados
    styles = getSampleStyleSheet()
    
    # Estilo para título principal
    title_style = ParagraphStyle(
        'AITitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1565C0'),
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'AISubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=15,
        textColor=colors.HexColor('#2E7D32'),
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#2E7D32'),
        borderPadding=5
    )
    
    # Estilo para secciones
    section_style = ParagraphStyle(
        'AISection',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#D32F2F'),
        fontName='Helvetica-Bold'
    )
    
    # Estilo para texto normal mejorado
    normal_style = ParagraphStyle(
        'AINormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        fontName='Helvetica',
        alignment=TA_JUSTIFY,
        leftIndent=10
    )
    
    # Estilo para destacados
    highlight_style = ParagraphStyle(
        'AIHighlight',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=10,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#FF6F00'),
        backColor=colors.HexColor('#FFF3E0'),
        borderWidth=1,
        borderColor=colors.HexColor('#FF6F00'),
        borderPadding=8,
        alignment=TA_CENTER
    )
    
    # ===== PORTADA PROFESIONAL =====
    story.append(Spacer(1, 30))
    
    # Logo y encabezado
    story.append(Paragraph("🤖 ANÁLISIS FINANCIERO INTELIGENTE", title_style))
    story.append(Spacer(1, 20))
    
    # Información de la empresa
    empresa_info = f"""
    <b>Empresa:</b> {empresa.nombre}<br/>
    <b>Sector:</b> {datos_empresa['categoria'].title()}<br/>
    <b>Ubicación:</b> {datos_empresa['ubicacion']}<br/>
    <b>Fecha de Análisis:</b> {datetime.now().strftime('%d de %B de %Y')}<br/>
    <b>Generado por:</b> CONTAFY AI Agent
    """
    story.append(Paragraph(empresa_info, normal_style))
    story.append(Spacer(1, 30))
    
    # Línea divisoria elegante
    story.append(Paragraph("<hr width='80%' color='#1565C0' size='2'/>", normal_style))
    story.append(Spacer(1, 20))
    
    # ===== RESUMEN EJECUTIVO IA =====
    story.append(Paragraph("📊 RESUMEN EJECUTIVO", subtitle_style))
    story.append(Paragraph(analisis_ia.get('resumen', 'Análisis no disponible'), highlight_style))
    story.append(Spacer(1, 20))
    
    # Métricas clave en tabla elegante
    metricas_data = [
        ['💰 Métrica Financiera', '📈 Valor Actual', '🎯 Estado', '📋 Análisis IA'],
        ['Ventas Mensuales', f"${datos_empresa['ventas_mes']:,.2f}", 
         '✅ Positivo' if datos_empresa['ventas_mes'] > 0 else '⚠️ Atención',
         'Ingresos del último mes'],
        ['Utilidad Neta', f"${datos_empresa['utilidad_mes']:,.2f}",
         '✅ Rentable' if datos_empresa['utilidad_mes'] > 0 else '❌ Pérdidas',
         'Beneficio después de gastos'],
        ['Margen de Utilidad', f"{datos_empresa['margen_mes']:.1f}%",
         '✅ Excelente' if datos_empresa['margen_mes'] > 20 else '⚠️ Mejorable' if datos_empresa['margen_mes'] > 10 else '❌ Crítico',
         'Eficiencia operativa'],
        ['Liquidez', f"{datos_empresa['liquidez']:.2f}",
         '✅ Saludable' if datos_empresa['liquidez'] > 1.5 else '⚠️ Riesgo',
         'Capacidad de pago'],
        ['ROE', f"{datos_empresa['roe']:.1f}%",
         '✅ Bueno' if datos_empresa['roe'] > 15 else '⚠️ Regular',
         'Retorno sobre capital']
    ]
    
    metricas_table = Table(metricas_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 2.3*inch])
    metricas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E3F2FD')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#1565C0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#E3F2FD'), colors.white])
    ]))
    story.append(metricas_table)
    story.append(Spacer(1, 25))
    
    # ===== FORTALEZAS IDENTIFICADAS POR IA =====
    story.append(Paragraph("💪 FORTALEZAS IDENTIFICADAS", section_style))
    fortalezas = analisis_ia.get('fortalezas', ['No se identificaron fortalezas específicas'])
    for i, fortaleza in enumerate(fortalezas, 1):
        story.append(Paragraph(f"<b>{i}.</b> {fortaleza}", normal_style))
    story.append(Spacer(1, 20))
    
    # ===== DEBILIDADES Y ÁREAS DE MEJORA =====
    story.append(Paragraph("⚠️ ÁREAS DE MEJORA", section_style))
    debilidades = analisis_ia.get('debilidades', ['No se identificaron debilidades específicas'])
    for i, debilidad in enumerate(debilidades, 1):
        story.append(Paragraph(f"<b>{i}.</b> {debilidad}", normal_style))
    story.append(Spacer(1, 20))
    
    # ===== OPORTUNIDADES DE CRECIMIENTO =====
    story.append(Paragraph("🚀 OPORTUNIDADES DE CRECIMIENTO", section_style))
    oportunidades = analisis_ia.get('oportunidades', ['No se identificaron oportunidades específicas'])
    for i, oportunidad in enumerate(oportunidades, 1):
        story.append(Paragraph(f"<b>{i}.</b> {oportunidad}", normal_style))
    story.append(Spacer(1, 20))
    
    # ===== PLAN DE ACCIÓN INMEDIATA =====
    story.append(Paragraph("⚡ PLAN DE ACCIÓN INMEDIATA", subtitle_style))
    acciones = analisis_ia.get('acciones_inmediatas', ['No se definieron acciones específicas'])
    
    acciones_data = [['🎯 Acción Recomendada', '⏱️ Prioridad', '📅 Plazo']]
    for i, accion in enumerate(acciones):
        prioridad = 'Alta' if i < 2 else 'Media'
        plazo = '1-2 semanas' if i < 2 else '1 mes'
        acciones_data.append([accion, prioridad, plazo])
    
    acciones_table = Table(acciones_data, colWidths=[4*inch, 1*inch, 1.5*inch])
    acciones_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D32F2F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFEBEE')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D32F2F')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 10)
    ]))
    story.append(acciones_table)
    story.append(Spacer(1, 25))
    
    # ===== PREDICCIÓN Y PROYECCIÓN =====
    story.append(Paragraph("🔮 PREDICCIÓN PARA EL PRÓXIMO MES", section_style))
    prediccion = analisis_ia.get('prediccion_proximo_mes', 'No hay predicción disponible')
    story.append(Paragraph(prediccion, highlight_style))
    story.append(Spacer(1, 20))
    
    # ===== RECOMENDACIÓN PRINCIPAL =====
    story.append(Paragraph("🎯 RECOMENDACIÓN PRINCIPAL", section_style))
    recomendacion = analisis_ia.get('recomendacion_principal', 'No hay recomendación específica')
    story.append(Paragraph(recomendacion, highlight_style))
    story.append(Spacer(1, 25))
    
    # ===== ANÁLISIS DE PRODUCTOS TOP =====
    if datos_empresa['top_productos']:
        story.append(Paragraph("🏆 ANÁLISIS DE PRODUCTOS ESTRELLA", section_style))
        
        productos_data = [['🛍️ Producto', '💰 Ventas', '📦 Cantidad', '📊 % del Total']]
        total_ventas_productos = sum(p['total_vendido'] for p in datos_empresa['top_productos'])
        
        for producto in datos_empresa['top_productos'][:5]:
            porcentaje = (producto['total_vendido'] / total_ventas_productos * 100) if total_ventas_productos > 0 else 0
            productos_data.append([
                producto['producto__nombre'][:25] + '...' if len(producto['producto__nombre']) > 25 else producto['producto__nombre'],
                f"${producto['total_vendido']:,.2f}",
                f"{producto['cantidad_vendida']} unidades",
                f"{porcentaje:.1f}%"
            ])
        
        productos_table = Table(productos_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1*inch])
        productos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E8F5E8')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2E7D32')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 10)
        ]))
        story.append(productos_table)
        story.append(Spacer(1, 20))
    
    # ===== ANÁLISIS DE GASTOS PRINCIPALES =====
    if datos_empresa['top_gastos']:
        story.append(Paragraph("💸 ANÁLISIS DE GASTOS PRINCIPALES", section_style))
        
        gastos_data = [['📋 Concepto', '💰 Monto', '📊 % del Total']]
        total_gastos_top = sum(g['total'] for g in datos_empresa['top_gastos'])
        
        for gasto in datos_empresa['top_gastos'][:5]:
            porcentaje = (gasto['total'] / total_gastos_top * 100) if total_gastos_top > 0 else 0
            gastos_data.append([
                gasto['descripcion'][:30] + '...' if len(gasto['descripcion']) > 30 else gasto['descripcion'],
                f"${gasto['total']:,.2f}",
                f"{porcentaje:.1f}%"
            ])
        
        gastos_table = Table(gastos_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        gastos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6F00')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF3E0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#FF6F00')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 10)
        ]))
        story.append(gastos_table)
        story.append(Spacer(1, 20))
    
    # ===== CONCLUSIONES Y PRÓXIMOS PASOS =====
    story.append(Paragraph("📋 CONCLUSIONES Y PRÓXIMOS PASOS", subtitle_style))
    
    conclusiones_text = f"""
    <b>Estado Actual:</b> Tu empresa {empresa.nombre} presenta {'una situación financiera saludable' if datos_empresa['utilidad_mes'] > 0 else 'desafíos financieros que requieren atención inmediata'}.
    
    <b>Indicadores Clave:</b>
    • Margen de utilidad del {datos_empresa['margen_mes']:.1f}% {'está por encima del promedio' if datos_empresa['margen_mes'] > 15 else 'necesita mejoras'}
    • Liquidez de {datos_empresa['liquidez']:.2f} {'indica buena capacidad de pago' if datos_empresa['liquidez'] > 1.2 else 'sugiere riesgo de liquidez'}
    • ROE del {datos_empresa['roe']:.1f}% {'muestra buen retorno sobre el capital' if datos_empresa['roe'] > 10 else 'indica necesidad de optimización'}
    
    <b>Próximos Pasos Recomendados:</b>
    1. Implementar las acciones inmediatas identificadas
    2. Monitorear semanalmente los indicadores clave
    3. Revisar mensualmente el progreso con este reporte IA
    4. Ajustar estrategias según los resultados obtenidos
    """
    
    story.append(Paragraph(conclusiones_text, normal_style))
    story.append(Spacer(1, 25))
    
    # ===== PIE DE PÁGINA PROFESIONAL =====
    story.append(Spacer(1, 30))
    story.append(Paragraph("<hr width='100%' color='#1565C0' size='2'/>", normal_style))
    story.append(Spacer(1, 15))
    
    footer_text = f"""
    <b>📊 REPORTE GENERADO POR CONTAFY AI</b><br/>
    Fecha: {datetime.now().strftime('%d de %B de %Y a las %H:%M')}<br/>
    Empresa: {empresa.nombre}<br/>
    Sistema: CONTAFY - Plataforma Inteligente para PYMES<br/>
    <i>Este análisis ha sido generado automáticamente usando inteligencia artificial avanzada</i>
    """
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        spaceAfter=10
    )
    
    story.append(Paragraph(footer_text, footer_style))
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="analisis_ia_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    return response

@login_required
def vista_reporte_ia(request):
    """Vista para mostrar el reporte de IA en el template"""
    empresa = request.user.empresa
    
    # Obtener análisis de IA
    ai_agent = ContafyAIAgent()
    analisis_ia = ai_agent.analizar_empresa(empresa)
    datos_empresa = ai_agent.obtener_datos_empresa(empresa)
    
    context = {
        'analisis_ia': analisis_ia,
        'datos_empresa': datos_empresa,
        'empresa': empresa
    }
    
    return render(request, 'empresa/reporte_ia.html', context)