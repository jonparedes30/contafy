import json
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np

from empresa.models import Venta, Gasto, Producto, Compra, Empresa, MetaFinanciera, CuentaContable, MovimientoContable
from empresa.views.resumen import obtener_totales_contables

@login_required
def exportar_excel_ventas(request):
    """Exporta solo las ventas filtradas a Excel, con los mismos filtros y columnas que la vista de historial de ventas."""
    try:
        empresa = request.user.empresa
        output = BytesIO()
        # --- Filtros igual que en listar_ventas ---
        ventas = Venta.objects.filter(empresa=empresa).order_by('-fecha')
        buscar = request.GET.get('buscar', '').strip()
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        monto = request.GET.get('monto')
        if buscar:
            ventas = ventas.filter(
                Q(producto__nombre__icontains=buscar) |
                Q(producto__codigo__icontains=buscar) |
                Q(cliente__icontains=buscar)
            )
        if fecha_desde:
            ventas = ventas.filter(fecha__date__gte=fecha_desde)
        if fecha_hasta:
            ventas = ventas.filter(fecha__date__lte=fecha_hasta)
        if monto:
            if '-' in monto:
                min_monto, max_monto = monto.split('-')
                ventas = ventas.filter(monto__gte=float(min_monto), monto__lte=float(max_monto))
            elif monto.endswith('+'):
                min_monto = monto.replace('+', '')
                ventas = ventas.filter(monto__gte=float(min_monto))
        # --- Exportar solo la hoja de ventas filtradas ---
        ventas_data = list(ventas.values(
            'fecha', 'producto__nombre', 'cliente', 'cantidad', 'precio_unitario', 'total'
        ))
        df_ventas = pd.DataFrame(ventas_data)
        # Renombrar columnas para que coincidan con la tabla HTML
        df_ventas.rename(columns={
            'fecha': 'Fecha',
            'producto__nombre': 'Producto',
            'cliente': 'Cliente',
            'cantidad': 'Cantidad',
            'precio_unitario': 'Precio Unitario',
            'total': 'Total (USD)'
        }, inplace=True)
        # Formatear fecha y montos
        if 'Fecha' in df_ventas.columns:
            df_ventas['Fecha'] = pd.to_datetime(df_ventas['Fecha']).dt.strftime('%d/%m/%Y %H:%M')
        if 'Precio Unitario' in df_ventas.columns:
            df_ventas['Precio Unitario'] = df_ventas['Precio Unitario'].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")
        if 'Total (USD)' in df_ventas.columns:
            df_ventas['Total (USD)'] = df_ventas['Total (USD)'].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")
        # Escribir a Excel
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_ventas.to_excel(writer, sheet_name='Ventas', index=False)
            worksheet = writer.sheets['Ventas']
            workbook = writer.book
            
            # ===== MEJORAS DE FORMATO Y VISUAL =====
            # Aplicar zoom para mejor visibilidad
            worksheet.set_zoom(110)
            
            # Formato de encabezado mejorado con colores atractivos
            header_format = workbook.add_format({
                'bold': True, 
                'bg_color': '#2E86AB', 
                'font_color': 'white', 
                'border': 1, 
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 12,
                'font_name': 'Arial'
            })
            
            # Formato para datos con bordes uniformes y colores claros
            data_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial'
            })
            
            # Formato para columnas de texto largo con wrap_text
            text_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'text_wrap': True
            })
            
            # Formato para números y montos
            number_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'num_format': '#,##0'
            })
            
            money_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'num_format': '$#,##0.00'
            })
            
            # Aplicar formatos y configurar columnas
            for col_num, value in enumerate(df_ventas.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
                # Configurar anchos de columna optimizados
                if col_num == 0:  # Fecha
                    worksheet.set_column(col_num, col_num, 18)
                elif col_num == 1:  # Producto
                    worksheet.set_column(col_num, col_num, 25, text_format)
                elif col_num == 2:  # Cliente
                    worksheet.set_column(col_num, col_num, 20, text_format)
                elif col_num == 3:  # Cantidad
                    worksheet.set_column(col_num, col_num, 12, number_format)
                elif col_num == 4:  # Precio Unitario
                    worksheet.set_column(col_num, col_num, 15, money_format)
                elif col_num == 5:  # Total
                    worksheet.set_column(col_num, col_num, 15, money_format)
            
            # Aplicar formato a todas las filas de datos
            for row_num in range(1, len(df_ventas) + 1):
                for col_num in range(len(df_ventas.columns)):
                    if col_num in [1, 2]:  # Columnas de texto
                        worksheet.write(row_num, col_num, df_ventas.iloc[row_num-1, col_num], text_format)
                    elif col_num == 3:  # Cantidad
                        worksheet.write(row_num, col_num, df_ventas.iloc[row_num-1, col_num], number_format)
                    elif col_num in [4, 5]:  # Columnas monetarias
                        worksheet.write(row_num, col_num, df_ventas.iloc[row_num-1, col_num], money_format)
                    else:  # Fecha
                        worksheet.write(row_num, col_num, df_ventas.iloc[row_num-1, col_num], data_format)
            
            # Congelar primera fila y primera columna
            worksheet.freeze_panes(1, 1)
            
            # Aplicar filtros automáticos
            worksheet.autofilter(0, 0, len(df_ventas), len(df_ventas.columns)-1)
            
            # ===== VISUALIZACIONES EXTRA =====
            # Crear hoja de análisis mensual con gráfico
            if len(df_ventas) > 0:
                # Agrupar ventas por mes
                df_ventas['Fecha_Date'] = pd.to_datetime(df_ventas['Fecha'], format='%d/%m/%Y %H:%M')
                df_ventas['Mes'] = df_ventas['Fecha_Date'].dt.strftime('%B %Y')
                ventas_mensuales = df_ventas.groupby('Mes')['Total (USD)'].sum().reset_index()
                
                # Crear hoja de análisis mensual
                ventas_mensuales.to_excel(writer, sheet_name='Análisis Mensual', index=False)
                analysis_worksheet = writer.sheets['Análisis Mensual']
                
                # Formato para la hoja de análisis
                analysis_worksheet.set_zoom(110)
                analysis_worksheet.set_column('A:A', 20, text_format)
                analysis_worksheet.set_column('B:B', 18, money_format)
                
                # Aplicar encabezados
                for col_num, value in enumerate(ventas_mensuales.columns.values):
                    analysis_worksheet.write(0, col_num, value, header_format)
                
                # Crear gráfico de línea para ventas mensuales
                chart = workbook.add_chart({'type': 'line'})
                
                # Agregar datos al gráfico
                chart.add_series({
                    'name': 'Ventas Mensuales',
                    'categories': f'=Análisis Mensual!$A$2:$A${len(ventas_mensuales)+1}',
                    'values': f'=Análisis Mensual!$B$2:$B${len(ventas_mensuales)+1}',
                    'line': {'width': 3, 'color': '#2E86AB'},
                    'marker': {'type': 'circle', 'size': 8, 'fill': {'color': '#2E86AB'}}
                })
                
                # Configurar el gráfico
                chart.set_title({'name': 'Tendencia de Ventas Mensuales', 'name_font': {'size': 14, 'bold': True}})
                chart.set_x_axis({'name': 'Mes', 'name_font': {'size': 12}})
                chart.set_y_axis({'name': 'Total Ventas (USD)', 'name_font': {'size': 12}})
                chart.set_size({'width': 600, 'height': 400})
                
                # Insertar gráfico en la hoja de análisis
                analysis_worksheet.insert_chart('D2', chart)
                
                # Crear hoja de top productos con gráfico de barras
                top_productos = df_ventas.groupby('Producto')['Total (USD)'].sum().sort_values(ascending=False).head(10).reset_index()
                top_productos.to_excel(writer, sheet_name='Top Productos', index=False)
                top_worksheet = writer.sheets['Top Productos']
                
                # Formato para la hoja de top productos
                top_worksheet.set_zoom(110)
                top_worksheet.set_column('A:A', 25, text_format)
                top_worksheet.set_column('B:B', 18, money_format)
                
                # Aplicar encabezados
                for col_num, value in enumerate(top_productos.columns.values):
                    top_worksheet.write(0, col_num, value, header_format)
                
                # Crear gráfico de barras para top productos
                bar_chart = workbook.add_chart({'type': 'bar'})
                
                # Agregar datos al gráfico de barras
                bar_chart.add_series({
                    'name': 'Ventas por Producto',
                    'categories': f'=Top Productos!$A$2:$A${len(top_productos)+1}',
                    'values': f'=Top Productos!$B$2:$B${len(top_productos)+1}',
                    'fill': {'color': '#2E86AB'},
                    'border': {'color': '#1B4F72'}
                })
                
                # Configurar el gráfico de barras
                bar_chart.set_title({'name': 'Top 10 Productos por Ventas', 'name_font': {'size': 14, 'bold': True}})
                bar_chart.set_x_axis({'name': 'Producto', 'name_font': {'size': 12}})
                bar_chart.set_y_axis({'name': 'Total Ventas (USD)', 'name_font': {'size': 12}})
                bar_chart.set_size({'width': 700, 'height': 500})
                
                # Insertar gráfico en la hoja de top productos
                top_worksheet.insert_chart('D2', bar_chart)
        
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="ventas_filtradas_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        return response
    except Exception as e:
        print(f"Error general en exportar_excel: {e}")
        return HttpResponse(f"Error al exportar Excel: {str(e)}", status=500)

@login_required
def exportar_excel_compras(request):
    """Exporta solo las compras filtradas a Excel, con los mismos filtros y columnas que la vista de historial de compras."""
    try:
        empresa = request.user.empresa
        output = BytesIO()
        # --- Filtros igual que en listar_compras ---
        compras = Compra.objects.filter(empresa=empresa).order_by('-fecha')
        buscar = request.GET.get('buscar', '').strip()
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        monto = request.GET.get('monto')
        if buscar:
            compras = compras.filter(
                Q(producto__nombre__icontains=buscar) |
                Q(producto__codigo__icontains=buscar)
            )
        if fecha_desde:
            compras = compras.filter(fecha__date__gte=fecha_desde)
        if fecha_hasta:
            compras = compras.filter(fecha__date__lte=fecha_hasta)
        if monto:
            if '-' in monto:
                min_monto, max_monto = monto.split('-')
                compras = compras.filter(monto__gte=float(min_monto), monto__lte=float(max_monto))
            elif monto.endswith('+'):
                min_monto = monto.replace('+', '')
                compras = compras.filter(monto__gte=float(min_monto))
        # --- Exportar solo la hoja de compras filtradas ---
        compras_data = list(compras.values(
            'fecha', 'producto__nombre', 'proveedor', 'cantidad', 'total'
        ))
        df_compras = pd.DataFrame(compras_data)
        # Calcular precio unitario
        df_compras['precio_unitario'] = df_compras.apply(
            lambda row: row['total'] / row['cantidad'] if row['cantidad'] > 0 else 0, axis=1
        )
        # Renombrar columnas para que coincidan con la tabla HTML
        df_compras.rename(columns={
            'fecha': 'Fecha',
            'producto__nombre': 'Producto',
            'proveedor': 'Proveedor',
            'cantidad': 'Cantidad',
            'precio_unitario': 'Precio Unitario',
            'total': 'Total (USD)'
        }, inplace=True)
        # Formatear fecha y montos
        if 'Fecha' in df_compras.columns:
            df_compras['Fecha'] = pd.to_datetime(df_compras['Fecha']).dt.strftime('%d/%m/%Y %H:%M')
        if 'Precio Unitario' in df_compras.columns:
            df_compras['Precio Unitario'] = df_compras['Precio Unitario'].map(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "")
        if 'Total (USD)' in df_compras.columns:
            df_compras['Total (USD)'] = df_compras['Total (USD)'].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")
        # Escribir a Excel
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_compras.to_excel(writer, sheet_name='Compras', index=False)
            worksheet = writer.sheets['Compras']
            workbook = writer.book
            
            # ===== MEJORAS DE FORMATO Y VISUAL =====
            # Aplicar zoom para mejor visibilidad
            worksheet.set_zoom(110)
            
            # Formato de encabezado mejorado con colores atractivos (paleta diferente)
            header_format = workbook.add_format({
                'bold': True, 
                'bg_color': '#A23B72', 
                'font_color': 'white', 
                'border': 1, 
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 12,
                'font_name': 'Arial'
            })
            
            # Formato para datos con bordes uniformes y colores claros
            data_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial'
            })
            
            # Formato para columnas de texto largo con wrap_text
            text_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'text_wrap': True
            })
            
            # Formato para números y montos
            number_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'num_format': '#,##0'
            })
            
            money_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'num_format': '$#,##0.00'
            })
            
            # Aplicar formatos y configurar columnas
            for col_num, value in enumerate(df_compras.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
                # Configurar anchos de columna optimizados
                if col_num == 0:  # Fecha
                    worksheet.set_column(col_num, col_num, 18)
                elif col_num == 1:  # Producto
                    worksheet.set_column(col_num, col_num, 25, text_format)
                elif col_num == 2:  # Proveedor
                    worksheet.set_column(col_num, col_num, 20, text_format)
                elif col_num == 3:  # Cantidad
                    worksheet.set_column(col_num, col_num, 12, number_format)
                elif col_num == 4:  # Precio Unitario
                    worksheet.set_column(col_num, col_num, 15, money_format)
                elif col_num == 5:  # Total
                    worksheet.set_column(col_num, col_num, 15, money_format)
            
            # Aplicar formato a todas las filas de datos
            for row_num in range(1, len(df_compras) + 1):
                for col_num in range(len(df_compras.columns)):
                    if col_num in [1, 2]:  # Columnas de texto
                        worksheet.write(row_num, col_num, df_compras.iloc[row_num-1, col_num], text_format)
                    elif col_num == 3:  # Cantidad
                        worksheet.write(row_num, col_num, df_compras.iloc[row_num-1, col_num], number_format)
                    elif col_num in [4, 5]:  # Columnas monetarias
                        worksheet.write(row_num, col_num, df_compras.iloc[row_num-1, col_num], money_format)
                    else:  # Fecha
                        worksheet.write(row_num, col_num, df_compras.iloc[row_num-1, col_num], data_format)
            
            # Congelar primera fila y primera columna
            worksheet.freeze_panes(1, 1)
            
            # Aplicar filtros automáticos
            worksheet.autofilter(0, 0, len(df_compras), len(df_compras.columns)-1)
            
            # ===== VISUALIZACIONES EXTRA =====
            # Crear hoja de análisis mensual con gráfico
            if len(df_compras) > 0:
                # Agrupar compras por mes
                df_compras['Fecha_Date'] = pd.to_datetime(df_compras['Fecha'], format='%d/%m/%Y %H:%M')
                df_compras['Mes'] = df_compras['Fecha_Date'].dt.strftime('%B %Y')
                compras_mensuales = df_compras.groupby('Mes')['Total (USD)'].sum().reset_index()
                
                # Crear hoja de análisis mensual
                compras_mensuales.to_excel(writer, sheet_name='Análisis Mensual', index=False)
                analysis_worksheet = writer.sheets['Análisis Mensual']
                
                # Formato para la hoja de análisis
                analysis_worksheet.set_zoom(110)
                analysis_worksheet.set_column('A:A', 20, text_format)
                analysis_worksheet.set_column('B:B', 18, money_format)
                
                # Aplicar encabezados
                for col_num, value in enumerate(compras_mensuales.columns.values):
                    analysis_worksheet.write(0, col_num, value, header_format)
                
                # Crear gráfico de línea para compras mensuales
                chart = workbook.add_chart({'type': 'line'})
                
                # Agregar datos al gráfico
                chart.add_series({
                    'name': 'Compras Mensuales',
                    'categories': f'=Análisis Mensual!$A$2:$A${len(compras_mensuales)+1}',
                    'values': f'=Análisis Mensual!$B$2:$B${len(compras_mensuales)+1}',
                    'line': {'width': 3, 'color': '#A23B72'},
                    'marker': {'type': 'circle', 'size': 8, 'fill': {'color': '#A23B72'}}
                })
                
                # Configurar el gráfico
                chart.set_title({'name': 'Tendencia de Compras Mensuales', 'name_font': {'size': 14, 'bold': True}})
                chart.set_x_axis({'name': 'Mes', 'name_font': {'size': 12}})
                chart.set_y_axis({'name': 'Total Compras (USD)', 'name_font': {'size': 12}})
                chart.set_size({'width': 600, 'height': 400})
                
                # Insertar gráfico en la hoja de análisis
                analysis_worksheet.insert_chart('D2', chart)
                
                # Crear hoja de top proveedores con gráfico de barras
                top_proveedores = df_compras.groupby('Proveedor')['Total (USD)'].sum().sort_values(ascending=False).head(10).reset_index()
                top_proveedores.to_excel(writer, sheet_name='Top Proveedores', index=False)
                top_worksheet = writer.sheets['Top Proveedores']
                
                # Formato para la hoja de top proveedores
                top_worksheet.set_zoom(110)
                top_worksheet.set_column('A:A', 25, text_format)
                top_worksheet.set_column('B:B', 18, money_format)
                
                # Aplicar encabezados
                for col_num, value in enumerate(top_proveedores.columns.values):
                    top_worksheet.write(0, col_num, value, header_format)
                
                # Crear gráfico de barras para top proveedores
                bar_chart = workbook.add_chart({'type': 'bar'})
                
                # Agregar datos al gráfico de barras
                bar_chart.add_series({
                    'name': 'Compras por Proveedor',
                    'categories': f'=Top Proveedores!$A$2:$A${len(top_proveedores)+1}',
                    'values': f'=Top Proveedores!$B$2:$B${len(top_proveedores)+1}',
                    'fill': {'color': '#A23B72'},
                    'border': {'color': '#6B2C57'}
                })
                
                # Configurar el gráfico de barras
                bar_chart.set_title({'name': 'Top 10 Proveedores por Compras', 'name_font': {'size': 14, 'bold': True}})
                bar_chart.set_x_axis({'name': 'Proveedor', 'name_font': {'size': 12}})
                bar_chart.set_y_axis({'name': 'Total Compras (USD)', 'name_font': {'size': 12}})
                bar_chart.set_size({'width': 700, 'height': 500})
                
                # Insertar gráfico en la hoja de top proveedores
                top_worksheet.insert_chart('D2', bar_chart)
        
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="compras_filtradas_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        return response
    except Exception as e:
        print(f"Error general en exportar_excel_compras: {e}")
        return HttpResponse(f"Error al exportar Excel: {str(e)}", status=500)

@login_required
def exportar_excel_gastos(request):
    """Exporta solo los gastos filtrados a Excel, con los mismos filtros y columnas que la vista de historial de gastos."""
    try:
        empresa = request.user.empresa
        output = BytesIO()
        # --- Filtros igual que en listar_gastos ---
        gastos = Gasto.objects.filter(empresa=empresa).order_by('-fecha')
        buscar = request.GET.get('buscar', '').strip()
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        monto = request.GET.get('monto')
        categoria = request.GET.get('categoria')
        
        if buscar:
            gastos = gastos.filter(
                Q(descripcion__icontains=buscar) |
                Q(categoria__icontains=buscar)
            )
        if fecha_desde:
            gastos = gastos.filter(fecha__date__gte=fecha_desde)
        if fecha_hasta:
            gastos = gastos.filter(fecha__date__lte=fecha_hasta)
        if monto:
            if '-' in monto:
                min_monto, max_monto = monto.split('-')
                gastos = gastos.filter(monto__gte=float(min_monto), monto__lte=float(max_monto))
            elif monto.endswith('+'):
                min_monto = monto.replace('+', '')
                gastos = gastos.filter(monto__gte=float(min_monto))
        if categoria:
            gastos = gastos.filter(categoria=categoria)
        
        # --- Exportar solo la hoja de gastos filtrados ---
        gastos_data = list(gastos.values(
            'fecha', 'descripcion', 'categoria', 'monto'
        ))
        df_gastos = pd.DataFrame(gastos_data)
        
        # Renombrar columnas para que coincidan con la tabla HTML
        df_gastos.rename(columns={
            'fecha': 'Fecha',
            'descripcion': 'Concepto',
            'categoria': 'Categoría',
            'monto': 'Monto (USD)'
        }, inplace=True)
        
        # Formatear fecha y montos
        if 'Fecha' in df_gastos.columns:
            df_gastos['Fecha'] = pd.to_datetime(df_gastos['Fecha']).dt.strftime('%d/%m/%Y %H:%M')
        if 'Monto (USD)' in df_gastos.columns:
            df_gastos['Monto (USD)'] = df_gastos['Monto (USD)'].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")
        
        # Escribir a Excel
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_gastos.to_excel(writer, sheet_name='Gastos', index=False)
            worksheet = writer.sheets['Gastos']
            workbook = writer.book
            
            # ===== MEJORAS DE FORMATO Y VISUAL =====
            # Aplicar zoom para mejor visibilidad
            worksheet.set_zoom(110)
            
            # Formato de encabezado mejorado con colores atractivos (paleta diferente)
            header_format = workbook.add_format({
                'bold': True, 
                'bg_color': '#F18F01', 
                'font_color': 'white', 
                'border': 1, 
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 12,
                'font_name': 'Arial'
            })
            
            # Formato para datos con bordes uniformes y colores claros
            data_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial'
            })
            
            # Formato para columnas de texto largo con wrap_text
            text_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'text_wrap': True
            })
            
            # Formato para números y montos
            number_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'num_format': '#,##0'
            })
            
            money_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'num_format': '$#,##0.00'
            })
            
            # Aplicar formatos y configurar columnas
            for col_num, value in enumerate(df_gastos.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
                # Configurar anchos de columna optimizados
                if col_num == 0:  # Fecha
                    worksheet.set_column(col_num, col_num, 18)
                elif col_num == 1:  # Concepto
                    worksheet.set_column(col_num, col_num, 35, text_format)
                elif col_num == 2:  # Categoría
                    worksheet.set_column(col_num, col_num, 20, text_format)
                elif col_num == 3:  # Monto
                    worksheet.set_column(col_num, col_num, 15, money_format)
            
            # Aplicar formato a todas las filas de datos
            for row_num in range(1, len(df_gastos) + 1):
                for col_num in range(len(df_gastos.columns)):
                    if col_num in [1, 2]:  # Columnas de texto
                        worksheet.write(row_num, col_num, df_gastos.iloc[row_num-1, col_num], text_format)
                    elif col_num == 3:  # Monto
                        worksheet.write(row_num, col_num, df_gastos.iloc[row_num-1, col_num], money_format)
                    else:  # Fecha
                        worksheet.write(row_num, col_num, df_gastos.iloc[row_num-1, col_num], data_format)
            
            # Congelar primera fila y primera columna
            worksheet.freeze_panes(1, 1)
            
            # Aplicar filtros automáticos
            worksheet.autofilter(0, 0, len(df_gastos), len(df_gastos.columns)-1)
            
            # ===== VISUALIZACIONES EXTRA =====
            # Crear hoja de análisis mensual con gráfico
            if len(df_gastos) > 0:
                # Agrupar gastos por mes
                df_gastos['Fecha_Date'] = pd.to_datetime(df_gastos['Fecha'], format='%d/%m/%Y %H:%M')
                df_gastos['Mes'] = df_gastos['Fecha_Date'].dt.strftime('%B %Y')
                gastos_mensuales = df_gastos.groupby('Mes')['Monto (USD)'].sum().reset_index()
                
                # Crear hoja de análisis mensual
                gastos_mensuales.to_excel(writer, sheet_name='Análisis Mensual', index=False)
                analysis_worksheet = writer.sheets['Análisis Mensual']
                
                # Formato para la hoja de análisis
                analysis_worksheet.set_zoom(110)
                analysis_worksheet.set_column('A:A', 20, text_format)
                analysis_worksheet.set_column('B:B', 18, money_format)
                
                # Aplicar encabezados
                for col_num, value in enumerate(gastos_mensuales.columns.values):
                    analysis_worksheet.write(0, col_num, value, header_format)
                
                # Crear gráfico de línea para gastos mensuales
                chart = workbook.add_chart({'type': 'line'})
                
                # Agregar datos al gráfico
                chart.add_series({
                    'name': 'Gastos Mensuales',
                    'categories': f'=Análisis Mensual!$A$2:$A${len(gastos_mensuales)+1}',
                    'values': f'=Análisis Mensual!$B$2:$B${len(gastos_mensuales)+1}',
                    'line': {'width': 3, 'color': '#F18F01'},
                    'marker': {'type': 'circle', 'size': 8, 'fill': {'color': '#F18F01'}}
                })
                
                # Configurar el gráfico
                chart.set_title({'name': 'Tendencia de Gastos Mensuales', 'name_font': {'size': 14, 'bold': True}})
                chart.set_x_axis({'name': 'Mes', 'name_font': {'size': 12}})
                chart.set_y_axis({'name': 'Total Gastos (USD)', 'name_font': {'size': 12}})
                chart.set_size({'width': 600, 'height': 400})
                
                # Insertar gráfico en la hoja de análisis
                analysis_worksheet.insert_chart('D2', chart)
                
                # Crear hoja de gastos por categoría con gráfico circular
                gastos_categoria = df_gastos.groupby('Categoría')['Monto (USD)'].sum().sort_values(ascending=False).reset_index()
                gastos_categoria.to_excel(writer, sheet_name='Gastos por Categoría', index=False)
                cat_worksheet = writer.sheets['Gastos por Categoría']
                
                # Formato para la hoja de gastos por categoría
                cat_worksheet.set_zoom(110)
                cat_worksheet.set_column('A:A', 25, text_format)
                cat_worksheet.set_column('B:B', 18, money_format)
                
                # Aplicar encabezados
                for col_num, value in enumerate(gastos_categoria.columns.values):
                    cat_worksheet.write(0, col_num, value, header_format)
                
                # Crear gráfico circular para gastos por categoría
                pie_chart = workbook.add_chart({'type': 'pie'})
                
                # Agregar datos al gráfico circular
                pie_chart.add_series({
                    'name': 'Gastos por Categoría',
                    'categories': f'=Gastos por Categoría!$A$2:$A${len(gastos_categoria)+1}',
                    'values': f'=Gastos por Categoría!$B$2:$B${len(gastos_categoria)+1}',
                    'data_labels': {'percentage': True, 'category': True}
                })
                
                # Configurar el gráfico circular
                pie_chart.set_title({'name': 'Distribución de Gastos por Categoría', 'name_font': {'size': 14, 'bold': True}})
                pie_chart.set_size({'width': 500, 'height': 400})
                
                # Insertar gráfico en la hoja de gastos por categoría
                cat_worksheet.insert_chart('D2', pie_chart)
        
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="gastos_filtrados_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        return response
    except Exception as e:
        print(f"Error general en exportar_excel_gastos: {e}")
        return HttpResponse(f"Error al exportar Excel: {str(e)}", status=500)

@login_required
def exportar_pdf_usuario(request):
    """Exporta reporte PDF profesional para usuarios con análisis avanzados"""
    empresa = request.user.empresa
    totales = obtener_totales_contables(empresa)
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # ===== MEJORAS DE DISEÑO PROFESIONAL =====
    # Estilos mejorados
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.darkgreen,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=15,
        textColor=colors.darkred,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.fontName = 'Helvetica'
    
    # ===== PORTADA INICIAL =====
    story.append(Paragraph("📊 REPORTE FINANCIERO EMPRESARIAL", title_style))
    story.append(Spacer(1, 40))
    
    # Logo placeholder
    story.append(Paragraph("🏢 LOGO CONTAFY AQUÍ", ParagraphStyle(
        'LogoPlaceholder',
        parent=styles['Normal'],
        fontSize=16,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=30
    )))
    
    story.append(Paragraph(f"<b>Empresa:</b> {empresa.nombre}", normal_style))
    story.append(Paragraph(f"<b>Fecha de Generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    story.append(Paragraph(f"<b>Sistema:</b> CONTAFY - Plataforma de Gestión para PYMES", normal_style))
    story.append(Spacer(1, 30))
    
    # Línea divisoria
    story.append(Paragraph("<hr width='100%' color='#1976d2'/>", normal_style))
    story.append(Spacer(1, 20))
    
    # Encabezado
    story.append(Paragraph(f"REPORTE FINANCIERO PROFESIONAL", title_style))
    story.append(Paragraph(f"Empresa: {empresa.nombre}", subtitle_style))
    story.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    story.append(Spacer(1, 20))
    
    # Obtener datos
    ventas = Venta.objects.filter(empresa=empresa)
    gastos = Gasto.objects.filter(empresa=empresa)
    productos = Producto.objects.filter(empresa=empresa)
    
    # Análisis de Ventas
    story.append(Paragraph("ANÁLISIS DE VENTAS", subtitle_style))
    
    total_ventas = totales['ventas'] or 0
    total_ventas_count = ventas.count()
    promedio_venta = total_ventas / total_ventas_count if total_ventas_count > 0 else 0
    
    # Ventas por mes (últimos 6 meses)
    meses_atras = 6
    ventas_mensuales = []
    for i in range(meses_atras):
        fecha_inicio = timezone.now() - timedelta(days=30*(i+1))
        fecha_fin = timezone.now() - timedelta(days=30*i)
        venta_mes = ventas.filter(fecha__range=[fecha_inicio, fecha_fin]).aggregate(total=Sum('total'))['total'] or 0
        # Convertir a float para el gráfico
        ventas_mensuales.append(float(venta_mes))
    
    ventas_mensuales.reverse()
    
    # Crear gráfico de ventas mensuales
    drawing = Drawing(400, 200)
    chart = HorizontalLineChart()
    chart.x = 50
    chart.y = 50
    chart.height = 125
    chart.width = 300
    chart.data = [ventas_mensuales]
    chart.categoryAxis.categoryNames = [f'M{i+1}' for i in range(meses_atras)]
    chart.valueAxis.valueMin = 0
    from decimal import Decimal
    max_ventas = float(max(ventas_mensuales)) if ventas_mensuales else 1000.0
    chart.valueAxis.valueMax = max_ventas * 1.2
    chart.valueAxis.valueStep = max_ventas / 5
    chart.lines[0].strokeWidth = 3
    chart.lines[0].strokeColor = colors.blue
    
    drawing.add(chart)
    story.append(drawing)
    story.append(Spacer(1, 20))
    
    # Tabla de métricas de ventas mejorada
    ventas_data = [
        ['📈 Métrica', '💰 Valor', '📊 Análisis'],
        ['Total Ventas', f'${total_ventas:,.2f}', 'Ingresos totales generados'],
        ['Número de Ventas', str(total_ventas_count), 'Cantidad de transacciones'],
        ['Promedio por Venta', f'${promedio_venta:,.2f}', 'Ticket promedio'],
        ['Tendencia', '📈' if len(ventas_mensuales) >= 2 and ventas_mensuales[-1] > ventas_mensuales[-2] else '📉', 
         'Comparación mes anterior']
    ]
    
    ventas_table = Table(ventas_data, colWidths=[2*inch, 1.5*inch, 3*inch])
    ventas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightblue, colors.white])
    ]))
    story.append(ventas_table)
    story.append(Spacer(1, 20))
    
    # Análisis de Gastos
    story.append(Paragraph("ANÁLISIS DE GASTOS", subtitle_style))
    
    total_gastos = totales['gastos'] or 0
    gastos_por_categoria = gastos.values('categoria').annotate(total=Sum('monto')).order_by('-total')
    
    # Gráfico de gastos por categoría
    if gastos_por_categoria:
        drawing2 = Drawing(400, 200)
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 200
        pie.height = 200
        
        categorias = [item['categoria'] for item in gastos_por_categoria]
        valores = [float(item['total']) for item in gastos_por_categoria]
        
        pie.data = valores
        pie.labels = categorias
        pie.slices.strokeWidth = 0.5
        
        drawing2.add(pie)
        story.append(drawing2)
        story.append(Spacer(1, 20))
    
    # Tabla de gastos por categoría
    gastos_cat_data = [['Categoría', 'Total', '% del Total']]
    if gastos_por_categoria:
        for item in gastos_por_categoria:
            porcentaje = (item['total'] / total_gastos * 100) if total_gastos > 0 else 0
            gastos_cat_data.append([
                item['categoria'],
                f"${item['total']:,.2f}",
                f"{porcentaje:.1f}%"
            ])
    else:
        gastos_cat_data.append(['Sin datos', '$0.00', '0%'])
    
    gastos_table = Table(gastos_cat_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    gastos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(gastos_table)
    story.append(Spacer(1, 20))
    
    # Análisis de Rentabilidad
    story.append(Paragraph("ANÁLISIS DE RENTABILIDAD", subtitle_style))
    
    utilidad = total_ventas - total_gastos
    margen_utilidad = (utilidad / total_ventas * 100) if total_ventas > 0 else 0
    
    # Calcular indicadores financieros
    productos_count = productos.count()
    stock_total = productos.aggregate(total=Sum('stock'))['total'] or 0
    valor_inventario = sum(p.precio_unitario * p.stock for p in productos)
    
    # Rotación de inventario (aproximada)
    rotacion_inventario = total_ventas / valor_inventario if valor_inventario > 0 else 0
    
    rentabilidad_data = [
        ['Indicador', 'Valor', 'Interpretación'],
        ['Utilidad Neta', f'${utilidad:,.2f}', 'Beneficio después de gastos'],
        ['Margen de Utilidad', f'{margen_utilidad:.1f}%', 'Porcentaje de ganancia'],
        ['Rotación de Inventario', f'{rotacion_inventario:.2f}', 'Veces que se renueva el inventario'],
        ['Valor del Inventario', f'${valor_inventario:,.2f}', 'Capital invertido en stock'],
        ['Productos Activos', str(productos_count), 'Variedad de productos']
    ]
    
    rentabilidad_table = Table(rentabilidad_data, colWidths=[2*inch, 1.5*inch, 3*inch])
    rentabilidad_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(rentabilidad_table)
    story.append(Spacer(1, 20))
    
    # Análisis de Productos
    story.append(Paragraph("ANÁLISIS DE PRODUCTOS", subtitle_style))
    
    # Productos más vendidos
    productos_vendidos = ventas.values('producto__nombre').annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum('total')
    ).order_by('-total_ingresos')[:5]
    
    if productos_vendidos:
        productos_data = [['Producto', 'Cantidad Vendida', 'Ingresos Generados']]
        for item in productos_vendidos:
            productos_data.append([
                item['producto__nombre'],
                str(item['total_vendido']),
                f"${item['total_ingresos']:,.2f}"
            ])
        
        productos_table = Table(productos_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        productos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(productos_table)
        story.append(Spacer(1, 20))
    
    # Recomendaciones
    story.append(Paragraph("RECOMENDACIONES ESTRATÉGICAS", subtitle_style))
    
    recomendaciones = []
    
    if margen_utilidad < 20:
        recomendaciones.append("• Considerar aumentar precios o reducir costos para mejorar el margen de utilidad")
    
    if rotacion_inventario < 2:
        recomendaciones.append("• Revisar estrategia de inventario: algunos productos pueden estar obsoletos")
    
    if len(ventas_mensuales) >= 2 and ventas_mensuales[-1] < ventas_mensuales[-2]:
        recomendaciones.append("• Las ventas han disminuido este mes. Analizar causas y ajustar estrategia")
    
    if productos_count < 10:
        recomendaciones.append("• Considerar diversificar el catálogo de productos para aumentar ingresos")
    
    if not recomendaciones:
        recomendaciones.append("• Excelente rendimiento. Mantener las estrategias actuales")
    
    for rec in recomendaciones:
        story.append(Paragraph(rec, normal_style))
    
    story.append(Spacer(1, 20))
    
    # ===== PIE DE PÁGINA =====
    story.append(Spacer(1, 30))
    story.append(Paragraph("<hr width='100%' color='#1976d2'/>", normal_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Generado con CONTAFY – Plataforma de Gestión para PYMES",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=10
        )
    ))
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_usuario_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    return response

@login_required
def exportar_pdf_profesional(request):
    """Exporta reporte PDF profesional para bancos con análisis financieros avanzados"""
    empresa = request.user.empresa
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Estilos profesionales
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ProfessionalTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'ProfessionalSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.darkgreen,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=15,
        textColor=colors.darkred,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.fontName = 'Helvetica'
    
    # ===== PORTADA INICIAL PROFESIONAL =====
    story.append(Paragraph("🏦 REPORTE FINANCIERO PROFESIONAL", title_style))
    story.append(Spacer(1, 40))
    
    # Logo placeholder
    story.append(Paragraph("🏢 LOGO CONTAFY AQUÍ", ParagraphStyle(
        'LogoPlaceholder',
        parent=styles['Normal'],
        fontSize=16,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=30
    )))
    
    story.append(Paragraph(f"<b>Empresa:</b> {empresa.nombre}", normal_style))
    story.append(Paragraph(f"<b>Fecha de Análisis:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    story.append(Paragraph(f"<b>Período:</b> Últimos 12 meses", normal_style))
    story.append(Paragraph(f"<b>Sistema:</b> CONTAFY - Plataforma de Contabilidad para PYMES", normal_style))
    story.append(Spacer(1, 30))
    
    # Línea divisoria
    story.append(Paragraph("<hr width='100%' color='#1976d2'/>", normal_style))
    story.append(Spacer(1, 20))
    
    # Obtener datos
    ventas = Venta.objects.filter(empresa=empresa)
    gastos = Gasto.objects.filter(empresa=empresa)
    productos = Producto.objects.filter(empresa=empresa)
    
    # RESUMEN EJECUTIVO
    story.append(Paragraph("RESUMEN EJECUTIVO", section_style))
    
    total_ventas = totales['ventas'] or 0
    total_gastos = totales['gastos'] or 0
    utilidad = total_ventas - total_gastos
    margen_utilidad = (utilidad / total_ventas * 100) if total_ventas > 0 else 0
    
    resumen_data = [
        ['📊 Indicador Financiero', '💰 Valor', '📈 Estado', '📋 Análisis'],
        ['Ingresos Totales', f'${total_ventas:,.2f}', '✅', 'Base de ingresos de la empresa'],
        ['Gastos Totales', f'${total_gastos:,.2f}', '⚠️', 'Costos operativos'],
        ['Utilidad Neta', f'${utilidad:,.2f}', '✅' if utilidad > 0 else '❌', 'Rentabilidad del negocio'],
        ['Margen de Utilidad', f'{margen_utilidad:.1f}%', '✅' if margen_utilidad > 15 else '⚠️', 'Eficiencia operativa']
    ]
    
    resumen_table = Table(resumen_data, colWidths=[2*inch, 1.5*inch, 0.5*inch, 2.5*inch])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
    ]))
    story.append(resumen_table)
    story.append(Spacer(1, 25))
    
    # ANÁLISIS DE RENTABILIDAD
    story.append(Paragraph("ANÁLISIS DE RENTABILIDAD", section_style))
    
    # Calcular indicadores financieros avanzados
    valor_inventario = sum(p.precio_unitario * p.stock for p in productos)
    rotacion_inventario = total_ventas / valor_inventario if valor_inventario > 0 else 0
    
    # ROA (Return on Assets) - Retorno sobre activos
    activos_totales = valor_inventario  # Simplificado para este ejemplo
    roa = (utilidad / activos_totales * 100) if activos_totales > 0 else 0
    
    # Margen operativo
    margen_operativo = margen_utilidad  # Simplificado
    
    rentabilidad_data = [
        ['Indicador', 'Valor', 'Benchmark', 'Estado'],
        ['ROA (Retorno sobre Activos)', f'{roa:.2f}%', '>5%', '✓' if roa > 5 else '⚠'],
        ['Rotación de Inventario', f'{rotacion_inventario:.2f}', '>4', '✓' if rotacion_inventario > 4 else '⚠'],
        ['Margen Operativo', f'{margen_operativo:.1f}%', '>15%', '✓' if margen_operativo > 15 else '⚠'],
        ['Valor del Inventario', f'${valor_inventario:,.2f}', 'N/A', 'Capital invertido']
    ]
    
    rentabilidad_table = Table(rentabilidad_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 0.8*inch])
    rentabilidad_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(rentabilidad_table)
    story.append(Spacer(1, 25))
    
    # ANÁLISIS DE TENDENCIAS
    story.append(Paragraph("ANÁLISIS DE TENDENCIAS", section_style))
    
    # Ventas por mes (últimos 12 meses)
    ventas_mensuales = []
    meses_labels = []
    for i in range(12):
        fecha_inicio = timezone.now() - timedelta(days=30*(i+1))
        fecha_fin = timezone.now() - timedelta(days=30*i)
        venta_mes = ventas.filter(fecha__range=[fecha_inicio, fecha_fin]).aggregate(total=Sum('total'))['total'] or 0
        ventas_mensuales.append(venta_mes)
        meses_labels.append(f'{fecha_inicio.strftime("%b")}')
    
    ventas_mensuales.reverse()
    meses_labels.reverse()
    
    # Calcular crecimiento
    if len(ventas_mensuales) >= 2:
        if ventas_mensuales[-2] > 0:
            crecimiento = ((ventas_mensuales[-1] - ventas_mensuales[-2]) / ventas_mensuales[-2] * 100)
        else:
            crecimiento = 0
    else:
        crecimiento = 0

    # Evitar división por cero en estabilidad
    min_ventas = min(ventas_mensuales) if ventas_mensuales else 1
    if min_ventas == 0:
        estabilidad = 'N/A'
    else:
        estabilidad = 'Alta' if max(ventas_mensuales)/min_ventas < 2 else 'Media'

    tendencias_data = [
        ['Métrica', 'Valor', 'Interpretación'],
        ['Ventas Promedio Mensual', f'${sum(ventas_mensuales)/len(ventas_mensuales):,.2f}', 'Rendimiento promedio'],
        ['Mes de Mayor Ventas', f'${max(ventas_mensuales):,.2f}', 'Pico de rendimiento'],
        ['Mes de Menor Ventas', f'${min_ventas:,.2f}', 'Período de menor actividad'],
        ['Crecimiento vs Mes Anterior', f'{crecimiento:+.1f}%', 'Tendencia de crecimiento'],
        ['Estabilidad', estabilidad, 'Consistencia en ventas']
    ]
    
    tendencias_table = Table(tendencias_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
    tendencias_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightcoral),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(tendencias_table)
    story.append(Spacer(1, 25))
    
    # ANÁLISIS DE RIESGOS
    story.append(Paragraph("ANÁLISIS DE RIESGOS", section_style))
    
    # Calcular indicadores de riesgo
    gastos_fijos = gastos.filter(categoria='Fijo').aggregate(total=Sum('monto'))['total'] or 0
    gastos_variables = gastos.filter(categoria='Variable').aggregate(total=Sum('monto'))['total'] or 0
    
    # Ratio de cobertura de gastos
    cobertura_gastos = total_ventas / total_gastos if total_gastos > 0 else 0
    
    # Concentración de productos
    productos_vendidos = ventas.values('producto__nombre').annotate(total=Sum('total')).order_by('-total')
    if productos_vendidos:
        producto_principal = productos_vendidos[0]['total']
        concentracion = (producto_principal / total_ventas * 100) if total_ventas > 0 else 0
    else:
        concentracion = 0
    
    riesgos_data = [
        ['Factor de Riesgo', 'Valor', 'Nivel de Riesgo', 'Recomendación'],
        ['Cobertura de Gastos', f'{cobertura_gastos:.2f}x', 'Bajo' if cobertura_gastos > 1.5 else 'Alto', 
         'Mantener ratio > 1.5x'],
        ['Concentración Productos', f'{concentracion:.1f}%', 'Bajo' if concentracion < 30 else 'Alto',
         'Diversificar productos'],
        ['Gastos Fijos', f'{gastos_fijos/total_gastos*100:.1f}%' if total_gastos > 0 else '0%', 
         'Bajo' if gastos_fijos/total_gastos < 0.7 else 'Alto', 'Controlar gastos fijos'],
        ['Liquidez Operativa', f'{utilidad/total_gastos*100:.1f}%' if total_gastos > 0 else '0%',
         'Bajo' if utilidad/total_gastos > 0.2 else 'Alto', 'Mejorar eficiencia']
    ]
    
    riesgos_table = Table(riesgos_data, colWidths=[2*inch, 1*inch, 1*inch, 2.5*inch])
    riesgos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(riesgos_table)
    story.append(Spacer(1, 25))
    
    # PROYECCIONES FINANCIERAS
    story.append(Paragraph("PROYECCIONES FINANCIERAS", section_style))
    
    # Proyección simple basada en tendencias
    ventas_promedio = sum(ventas_mensuales) / len(ventas_mensuales) if ventas_mensuales else 0
    gastos_promedio = total_gastos / 12  # Simplificado
    
    # Proyección conservadora y optimista
    ventas_promedio = Decimal(ventas_promedio)
    proyeccion_conservadora = ventas_promedio * Decimal('0.9')  # -10%
    proyeccion_optimista = ventas_promedio * Decimal('1.2')     # +20%
    
    proyecciones_data = [
        ['Escenario', 'Ventas Mensuales', 'Utilidad Mensual', 'Margen'],
        ['Conservador', f'${proyeccion_conservadora:,.2f}', 
         f'${proyeccion_conservadora - gastos_promedio:,.2f}',
         f'{(proyeccion_conservadora - gastos_promedio)/proyeccion_conservadora*100:.1f}%'],
        ['Actual', f'${ventas_promedio:,.2f}', 
         f'${ventas_promedio - gastos_promedio:,.2f}',
         f'{(ventas_promedio - gastos_promedio)/ventas_promedio*100:.1f}%'],
        ['Optimista', f'${proyeccion_optimista:,.2f}', 
         f'${proyeccion_optimista - gastos_promedio:,.2f}',
         f'{(proyeccion_optimista - gastos_promedio)/proyeccion_optimista*100:.1f}%']
    ]
    
    proyecciones_table = Table(proyecciones_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
    proyecciones_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkviolet),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(proyecciones_table)
    story.append(Spacer(1, 25))
    
    # CERTIFICACIÓN PROFESIONAL
    story.append(Paragraph("CERTIFICACIÓN PROFESIONAL", section_style))
    
    certificacion_text = f"""
    Este reporte financiero ha sido generado automáticamente por el sistema CONTAFY 
    utilizando datos reales de la empresa {empresa.nombre}.
    
    Fecha de certificación: {datetime.now().strftime('%d/%m/%Y')}
    Sistema: CONTAFY - Plataforma de Contabilidad para PYMES
    Versión: 1.0
    
    Los datos presentados en este reporte corresponden a las transacciones registradas 
    en el sistema y han sido analizados utilizando metodologías financieras estándar.
    
    Este documento puede ser utilizado para:
    • Análisis crediticio
    • Evaluación de inversiones
    • Planificación estratégica
    • Cumplimiento regulatorio
    """
    
    story.append(Paragraph(certificacion_text, normal_style))
    story.append(Spacer(1, 20))
    
    # ===== PIE DE PÁGINA =====
    story.append(Spacer(1, 30))
    story.append(Paragraph("<hr width='100%' color='#1976d2'/>", normal_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Generado con CONTAFY – Plataforma de Gestión para PYMES",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=10
        )
    ))
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_profesional_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    return response

@login_required
def exportar_pdf(request):
    """Página de selección de tipo de reporte PDF"""
    return render(request, 'empresa/exportar_pdf.html')

@login_required
def exportar_excel_inventario(request):
    """Exporta el inventario filtrado a Excel"""
    try:
        empresa = request.user.empresa
        output = BytesIO()
        
        # Obtener parámetros de filtro
        buscar = request.GET.get('buscar', '')
        stock_filter = request.GET.get('stock', '')
        
        # Filtrar productos
        productos = Producto.objects.filter(empresa=empresa)
        
        if buscar:
            productos = productos.filter(
                Q(codigo__icontains=buscar) |
                Q(nombre__icontains=buscar) |
                Q(descripcion__icontains=buscar)
            )
        
        if stock_filter:
            if stock_filter == 'alto':
                productos = productos.filter(stock__gt=20)
            elif stock_filter == 'medio':
                productos = productos.filter(stock__gt=10, stock__lte=20)
            elif stock_filter == 'bajo':
                productos = productos.filter(stock__gt=0, stock__lte=10)
            elif stock_filter == 'agotado':
                productos = productos.filter(stock=0)
        
        # Ordenar por nombre
        productos = productos.order_by('nombre')
        
        # Preparar datos para Excel
        inventario_data = []
        for producto in productos:
            valor_total = producto.stock * (producto.precio_unitario or 0)
            inventario_data.append({
                'Código': producto.codigo,
                'Nombre': producto.nombre,
                'Descripción': producto.descripcion or '',
                'Stock Actual': producto.stock,
                'Precio Unitario': producto.precio_unitario or 0,
                'Precio de Venta (PVP)': producto.pvp or 0,
                'Valor Total': valor_total,
                'Estado': 'Alto Stock' if producto.stock > 20 else 'Stock Medio' if producto.stock > 10 else 'Bajo Stock' if producto.stock > 0 else 'Agotado'
            })
        
        df_inventario = pd.DataFrame(inventario_data)
        
        # Formatear columnas monetarias
        if 'Precio Unitario' in df_inventario.columns:
            df_inventario['Precio Unitario'] = df_inventario['Precio Unitario'].map(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "")
        if 'Precio de Venta (PVP)' in df_inventario.columns:
            df_inventario['Precio de Venta (PVP)'] = df_inventario['Precio de Venta (PVP)'].map(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "")
        if 'Valor Total' in df_inventario.columns:
            df_inventario['Valor Total'] = df_inventario['Valor Total'].map(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "")
        
        # Escribir a Excel
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_inventario.to_excel(writer, sheet_name='Inventario', index=False)
            worksheet = writer.sheets['Inventario']
            workbook = writer.book
            
            # ===== MEJORAS DE FORMATO Y VISUAL =====
            # Aplicar zoom para mejor visibilidad
            worksheet.set_zoom(110)
            
            # Formato de encabezado mejorado con colores atractivos (paleta diferente)
            header_format = workbook.add_format({
                'bold': True, 
                'bg_color': '#667eea', 
                'font_color': 'white', 
                'border': 1, 
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 12,
                'font_name': 'Arial'
            })
            
            # Formato para datos con bordes uniformes y colores claros
            data_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial'
            })
            
            # Formato para columnas de texto largo con wrap_text
            text_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'text_wrap': True
            })
            
            # Formato para números y montos
            number_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'num_format': '#,##0'
            })
            
            money_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'num_format': '$#,##0.00'
            })
            
            # Formato para estados con colores
            estado_alto_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#D4EDDA',
                'font_size': 10,
                'font_name': 'Arial',
                'font_color': '#155724'
            })
            
            estado_medio_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#FFF3CD',
                'font_size': 10,
                'font_name': 'Arial',
                'font_color': '#856404'
            })
            
            estado_bajo_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8D7DA',
                'font_size': 10,
                'font_name': 'Arial',
                'font_color': '#721C24'
            })
            
            estado_agotado_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F5C6CB',
                'font_size': 10,
                'font_name': 'Arial',
                'font_color': '#721C24',
                'bold': True
            })
            
            # Aplicar formatos y configurar columnas
            for col_num, value in enumerate(df_inventario.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
                # Configurar anchos de columna optimizados
                if col_num == 0:  # Código
                    worksheet.set_column(col_num, col_num, 15)
                elif col_num == 1:  # Nombre
                    worksheet.set_column(col_num, col_num, 25, text_format)
                elif col_num == 2:  # Descripción
                    worksheet.set_column(col_num, col_num, 30, text_format)
                elif col_num == 3:  # Stock Actual
                    worksheet.set_column(col_num, col_num, 12, number_format)
                elif col_num == 4:  # Precio Unitario
                    worksheet.set_column(col_num, col_num, 18, money_format)
                elif col_num == 5:  # Precio de Venta (PVP)
                    worksheet.set_column(col_num, col_num, 18, money_format)
                elif col_num == 6:  # Valor Total
                    worksheet.set_column(col_num, col_num, 15, money_format)
                elif col_num == 7:  # Estado
                    worksheet.set_column(col_num, col_num, 15)
            
            # Aplicar formato a todas las filas de datos
            for row_num in range(1, len(df_inventario) + 1):
                for col_num in range(len(df_inventario.columns)):
                    cell_value = df_inventario.iloc[row_num-1, col_num]
                    
                    if col_num in [1, 2]:  # Columnas de texto
                        worksheet.write(row_num, col_num, cell_value, text_format)
                    elif col_num == 3:  # Stock Actual
                        worksheet.write(row_num, col_num, cell_value, number_format)
                    elif col_num in [4, 5, 6]:  # Columnas monetarias
                        worksheet.write(row_num, col_num, cell_value, money_format)
                    elif col_num == 7:  # Estado
                        if cell_value == 'Alto Stock':
                            worksheet.write(row_num, col_num, cell_value, estado_alto_format)
                        elif cell_value == 'Stock Medio':
                            worksheet.write(row_num, col_num, cell_value, estado_medio_format)
                        elif cell_value == 'Bajo Stock':
                            worksheet.write(row_num, col_num, cell_value, estado_bajo_format)
                        elif cell_value == 'Agotado':
                            worksheet.write(row_num, col_num, cell_value, estado_agotado_format)
                        else:
                            worksheet.write(row_num, col_num, cell_value, data_format)
                    else:  # Código
                        worksheet.write(row_num, col_num, cell_value, data_format)
            
            # Congelar primera fila y primera columna
            worksheet.freeze_panes(1, 1)
            
            # Aplicar filtros automáticos
            worksheet.autofilter(0, 0, len(df_inventario), len(df_inventario.columns)-1)
            
            # ===== VISUALIZACIONES EXTRA =====
            # Crear hoja de análisis de stock con gráficos
            if len(df_inventario) > 0:
                # Análisis por estado de stock
                estado_stock = df_inventario['Estado'].value_counts().reset_index()
                estado_stock.columns = ['Estado', 'Cantidad']
                estado_stock.to_excel(writer, sheet_name='Análisis de Stock', index=False)
                analysis_worksheet = writer.sheets['Análisis de Stock']
                
                # Formato para la hoja de análisis
                analysis_worksheet.set_zoom(110)
                analysis_worksheet.set_column('A:A', 20, text_format)
                analysis_worksheet.set_column('B:B', 15, number_format)
                
                # Aplicar encabezados
                for col_num, value in enumerate(estado_stock.columns.values):
                    analysis_worksheet.write(0, col_num, value, header_format)
                
                # Crear gráfico circular para estado de stock
                pie_chart = workbook.add_chart({'type': 'pie'})
                
                # Agregar datos al gráfico circular
                pie_chart.add_series({
                    'name': 'Estado de Stock',
                    'categories': f'=Análisis de Stock!$A$2:$A${len(estado_stock)+1}',
                    'values': f'=Análisis de Stock!$B$2:$B${len(estado_stock)+1}',
                    'data_labels': {'percentage': True, 'category': True}
                })
                
                # Configurar el gráfico circular
                pie_chart.set_title({'name': 'Distribución del Estado de Stock', 'name_font': {'size': 14, 'bold': True}})
                pie_chart.set_size({'width': 500, 'height': 400})
                
                # Insertar gráfico en la hoja de análisis
                analysis_worksheet.insert_chart('D2', pie_chart)
                
                # Crear hoja de valor de inventario con gráfico de barras
                # Agrupar por estado y sumar valor total
                valor_por_estado = df_inventario.groupby('Estado')['Valor Total'].sum().reset_index()
                valor_por_estado.to_excel(writer, sheet_name='Valor por Estado', index=False)
                valor_worksheet = writer.sheets['Valor por Estado']
                
                # Formato para la hoja de valor por estado
                valor_worksheet.set_zoom(110)
                valor_worksheet.set_column('A:A', 20, text_format)
                valor_worksheet.set_column('B:B', 18, money_format)
                
                # Aplicar encabezados
                for col_num, value in enumerate(valor_por_estado.columns.values):
                    valor_worksheet.write(0, col_num, value, header_format)
                
                # Crear gráfico de barras para valor por estado
                bar_chart = workbook.add_chart({'type': 'bar'})
                
                # Agregar datos al gráfico de barras
                bar_chart.add_series({
                    'name': 'Valor por Estado',
                    'categories': f'=Valor por Estado!$A$2:$A${len(valor_por_estado)+1}',
                    'values': f'=Valor por Estado!$B$2:$B${len(valor_por_estado)+1}',
                    'fill': {'color': '#667eea'},
                    'border': {'color': '#4A5568'}
                })
                
                # Configurar el gráfico de barras
                bar_chart.set_title({'name': 'Valor Total del Inventario por Estado', 'name_font': {'size': 14, 'bold': True}})
                bar_chart.set_x_axis({'name': 'Estado', 'name_font': {'size': 12}})
                bar_chart.set_y_axis({'name': 'Valor Total (USD)', 'name_font': {'size': 12}})
                bar_chart.set_size({'width': 600, 'height': 400})
                
                # Insertar gráfico en la hoja de valor por estado
                valor_worksheet.insert_chart('D2', bar_chart)
        
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="inventario_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        return response
        
    except Exception as e:
        print(f"Error en exportar_excel_inventario: {e}")
        return HttpResponse(f"Error al exportar Excel: {str(e)}", status=500)

@login_required
def exportar_pdf_inventario(request):
    """Exporta el inventario filtrado a PDF"""
    try:
        empresa = request.user.empresa
        
        # Obtener parámetros de filtro
        buscar = request.GET.get('buscar', '')
        stock_filter = request.GET.get('stock', '')
        
        # Filtrar productos
        productos = Producto.objects.filter(empresa=empresa)
        
        if buscar:
            productos = productos.filter(
                Q(codigo__icontains=buscar) |
                Q(nombre__icontains=buscar) |
                Q(descripcion__icontains=buscar)
            )
        
        if stock_filter:
            if stock_filter == 'alto':
                productos = productos.filter(stock__gt=20)
            elif stock_filter == 'medio':
                productos = productos.filter(stock__gt=10, stock__lte=20)
            elif stock_filter == 'bajo':
                productos = productos.filter(stock__gt=0, stock__lte=10)
            elif stock_filter == 'agotado':
                productos = productos.filter(stock=0)
        
        # Ordenar por nombre
        productos = productos.order_by('nombre')
        
        # Calcular estadísticas
        total_productos = productos.count()
        productos_bajo_stock = productos.filter(stock__lte=10).count()
        total_inventario = sum(p.stock * (p.precio_unitario or 0) for p in productos)
        
        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.darkblue
        )
        normal_style = styles['Normal']
        
        # ===== PORTADA INICIAL =====
        story.append(Paragraph("📦 INVENTARIO - {empresa.nombre.upper()}", title_style))
        story.append(Spacer(1, 30))
        
        # Logo placeholder
        story.append(Paragraph("🏢 LOGO CONTAFY AQUÍ", ParagraphStyle(
            'LogoPlaceholder',
            parent=styles['Normal'],
            fontSize=16,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=30
        )))
        
        story.append(Paragraph(f"<b>Fecha de reporte:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
        story.append(Paragraph(f"<b>Sistema:</b> CONTAFY - Plataforma de Gestión para PYMES", normal_style))
        story.append(Spacer(1, 20))
        
        # Línea divisoria
        story.append(Paragraph("<hr width='100%' color='#1976d2'/>", normal_style))
        story.append(Spacer(1, 20))
        
        # Estadísticas
        story.append(Paragraph("ESTADÍSTICAS GENERALES", section_style))
        
        stats_data = [
            ['Métrica', 'Valor'],
            ['Total de Productos', str(total_productos)],
            ['Productos con Bajo Stock', str(productos_bajo_stock)],
            ['Valor Total del Inventario', f"${total_inventario:,.2f}"],
            ['Productos Agotados', str(productos.filter(stock=0).count())]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 25))
        
        # Tabla de inventario
        story.append(Paragraph("DETALLE DE INVENTARIO", section_style))
        
        # Preparar datos de la tabla
        table_data = [['Código', 'Producto', 'Stock', 'Precio Unit.', 'Valor Total', 'Estado']]
        
        for producto in productos:
            valor_total = producto.stock * (producto.precio_unitario or 0)
            estado = 'Alto Stock' if producto.stock > 20 else 'Stock Medio' if producto.stock > 10 else 'Bajo Stock' if producto.stock > 0 else 'Agotado'
            
            table_data.append([
                producto.codigo,
                producto.nombre[:30] + '...' if len(producto.nombre) > 30 else producto.nombre,
                str(producto.stock),
                f"${producto.precio_unitario:,.2f}" if producto.precio_unitario else "N/A",
                f"${valor_total:,.2f}" if valor_total > 0 else "N/A",
                estado
            ])
        
        # Crear tabla con paginación si es necesario
        if len(table_data) > 1:  # Si hay productos
            inventory_table = Table(table_data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 1*inch, 1.2*inch, 1*inch])
            inventory_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            story.append(inventory_table)
        else:
            story.append(Paragraph("No hay productos en el inventario.", normal_style))
        
        story.append(Spacer(1, 25))
        
        # Análisis de stock
        story.append(Paragraph("ANÁLISIS DE STOCK", section_style))
        
        alto_stock = productos.filter(stock__gt=20).count()
        medio_stock = productos.filter(stock__gt=10, stock__lte=20).count()
        bajo_stock = productos.filter(stock__gt=0, stock__lte=10).count()
        agotado = productos.filter(stock=0).count()
        
        analysis_data = [
            ['Estado de Stock', 'Cantidad', 'Porcentaje'],
            ['Alto Stock (>20)', str(alto_stock), f"{alto_stock/total_productos*100:.1f}%" if total_productos > 0 else "0%"],
            ['Stock Medio (11-20)', str(medio_stock), f"{medio_stock/total_productos*100:.1f}%" if total_productos > 0 else "0%"],
            ['Bajo Stock (1-10)', str(bajo_stock), f"{bajo_stock/total_productos*100:.1f}%" if total_productos > 0 else "0%"],
            ['Agotado (0)', str(agotado), f"{agotado/total_productos*100:.1f}%" if total_productos > 0 else "0%"]
        ]
        
        analysis_table = Table(analysis_data, colWidths=[2*inch, 1*inch, 1*inch])
        analysis_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightcoral),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        story.append(analysis_table)
        
        # ===== PIE DE PÁGINA =====
        story.append(Spacer(1, 30))
        story.append(Paragraph("<hr width='100%' color='#1976d2'/>", normal_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Generado con CONTAFY – Plataforma de Gestión para PYMES",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.grey,
                spaceAfter=10
            )
        ))
        
        # Generar PDF
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="inventario_{empresa.nombre}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        
        return response
        
    except Exception as e:
        print(f"Error en exportar_pdf_inventario: {e}")
        return HttpResponse(f"Error al exportar PDF: {str(e)}", status=500)

@login_required
def exportar_excel_completo(request):
    """Exporta un reporte Excel completo con todas las secciones de la empresa"""
    try:
        empresa = request.user.empresa
        totales = obtener_totales_contables(empresa)
        
        # Obtener todos los datos de la empresa
        ventas = Venta.objects.filter(empresa=empresa).order_by('-fecha')
        compras = Compra.objects.filter(empresa=empresa).order_by('-fecha')
        gastos = Gasto.objects.filter(empresa=empresa).order_by('-fecha')
        productos = Producto.objects.filter(empresa=empresa).order_by('nombre')
        
        # ===== CALCULAR DATOS CONTABLES =====
        # Obtener cuentas contables
        cuentas = CuentaContable.objects.filter(empresa=empresa)
        
        # Calcular datos del estado de resultados
        try:
            cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
            total_ventas_contable = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito'
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            total_ventas_contable = 0
            
        try:
            cuenta_inventario = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Inventario')
            total_costos = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_inventario, tipo='debito'
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            total_costos = 0
            
        try:
            cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
            total_gastos_contable = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_gastos, tipo='debito'
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            total_gastos_contable = 0
        
        # Calcular utilidades
        utilidad_operativa = total_ventas_contable - total_costos
        utilidad_neta = utilidad_operativa - total_gastos_contable
        
        # Calcular balance general
        activos = []
        pasivos = []
        capital = []
        total_activos = 0
        total_pasivos = 0
        total_capital = 0
        
        # Obtener movimientos para balance
        movimientos = MovimientoContable.objects.filter(empresa=empresa).values(
            'cuenta_fk', 'tipo'
        ).annotate(total=Sum('monto'))
        
        movimientos_dict = {}
        for mov in movimientos:
            key = (mov['cuenta_fk'], mov['tipo'])
            movimientos_dict[key] = mov['total']
        
        for cuenta in cuentas:
            debitos = movimientos_dict.get((cuenta.id, 'debito'), 0)
            creditos = movimientos_dict.get((cuenta.id, 'credito'), 0)
            
            if cuenta.tipo == 'activo':
                saldo = debitos - creditos
            else:
                saldo = creditos - debitos

            cuenta_dict = {
                'cuenta_fk__nombre': cuenta.nombre,
                'valor': saldo
            }
            
            if cuenta.tipo == 'activo':
                activos.append(cuenta_dict)
                total_activos += saldo
            elif cuenta.tipo == 'pasivo':
                pasivos.append(cuenta_dict)
                total_pasivos += saldo
            elif cuenta.tipo == 'capital':
                capital.append(cuenta_dict)
                total_capital += saldo
        
        total_patrimonio = total_activos - total_pasivos
        
        # Calcular flujo de caja
        try:
            cuenta_caja = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Caja/Banco')
            flujo_mensual = []
            meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
            
            for idx, mes_nombre in enumerate(meses, start=1):
                entradas = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_caja, tipo='debito',
                    fecha__year=datetime.now().year, fecha__month=idx
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                salidas = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_caja, tipo='credito',
                    fecha__year=datetime.now().year, fecha__month=idx
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                neto = entradas - salidas
                flujo_mensual.append({
                    'Mes': mes_nombre,
                    'Entradas': entradas,
                    'Salidas': salidas,
                    'Neto': neto
                })
        except CuentaContable.DoesNotExist:
            flujo_mensual = []
        
        # Crear buffer para el Excel
        output = BytesIO()
        
        # Crear Excel con múltiples hojas
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # ===== MEJORAS DE FORMATO Y VISUAL =====
            # Formato para encabezados mejorado
            header_format = workbook.add_format({
                'bold': True, 
                'bg_color': '#1976d2', 
                'font_color': 'white', 
                'border': 1, 
                'align': 'center', 
                'valign': 'vcenter',
                'font_size': 12,
                'font_name': 'Arial'
            })
            
            # Formato para datos con bordes uniformes y colores claros
            data_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial'
            })
            
            # Formato para columnas de texto largo con wrap_text
            text_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial',
                'text_wrap': True
            })
            
            # Formato para números monetarios
            money_format = workbook.add_format({
                'num_format': '$#,##0.00', 
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial'
            })
            
            # Formato para fechas
            date_format = workbook.add_format({
                'num_format': 'dd/mm/yyyy hh:mm', 
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial'
            })
            
            # Formato para números
            number_format = workbook.add_format({
                'num_format': '#,##0', 
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#F8F9FA',
                'font_size': 10,
                'font_name': 'Arial'
            })
            
            # 1. HOJA: RESUMEN EJECUTIVO MEJORADO
            resumen_data = [
                ['REPORTE FINANCIERO COMPLETO', ''],
                ['Empresa', empresa.nombre],
                ['Fecha del Reporte', datetime.now().strftime('%d/%m/%Y %H:%M')],
                ['', ''],
                ['ESTADO DE RESULTADOS', ''],
                ['Ventas Totales', total_ventas_contable],
                ['Costos de Ventas', total_costos],
                ['Utilidad Bruta', utilidad_operativa],
                ['Gastos Operativos', total_gastos_contable],
                ['Utilidad Neta', utilidad_neta],
                ['Margen Bruto (%)', (utilidad_operativa/total_ventas_contable*100) if total_ventas_contable > 0 else 0],
                ['Margen Neto (%)', (utilidad_neta/total_ventas_contable*100) if total_ventas_contable > 0 else 0],
                ['', ''],
                ['BALANCE GENERAL', ''],
                ['Total Activos', total_activos],
                ['Total Pasivos', total_pasivos],
                ['Total Patrimonio', total_patrimonio],
                ['', ''],
                ['ESTADÍSTICAS OPERATIVAS', ''],
                ['Total de Ventas Registradas', ventas.count()],
                ['Total de Compras Registradas', compras.count()],
                ['Total de Gastos Registrados', gastos.count()],
                ['Total de Productos', productos.count()],
                ['Productos con Stock', productos.filter(stock__gt=0).count()],
                ['Productos Agotados', productos.filter(stock=0).count()],
            ]
            
            df_resumen = pd.DataFrame(resumen_data, columns=['Concepto', 'Valor'])
            df_resumen.to_excel(writer, sheet_name='Resumen Ejecutivo', index=False)
            
            # Aplicar formato a la hoja de resumen
            worksheet = writer.sheets['Resumen Ejecutivo']
            # Aplicar zoom para mejor visibilidad
            worksheet.set_zoom(110)
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 25)
            # Congelar primera fila y primera columna
            worksheet.freeze_panes(1, 1)
            
            # Aplicar formato monetario a valores numéricos
            for row in range(5, 12):  # Filas con valores monetarios del estado de resultados
                worksheet.write(row, 1, resumen_data[row][1], money_format)
            for row in range(14, 17):  # Filas con valores monetarios del balance
                worksheet.write(row, 1, resumen_data[row][1], money_format)
            
            # 2. HOJA: ESTADO DE RESULTADOS
            estado_resultados_data = [
                ['ESTADO DE RESULTADOS', ''],
                ['Empresa', empresa.nombre],
                ['Período', f'{datetime.now().year}'],
                ['', ''],
                ['INGRESOS', ''],
                ['Ventas', total_ventas_contable],
                ['Total Ingresos', total_ventas_contable],
                ['', ''],
                ['COSTOS', ''],
                ['Costos de Ventas', total_costos],
                ['Total Costos', total_costos],
                ['', ''],
                ['UTILIDAD BRUTA', utilidad_operativa],
                ['', ''],
                ['GASTOS OPERATIVOS', ''],
                ['Gastos Administrativos', total_gastos_contable],
                ['Total Gastos', total_gastos_contable],
                ['', ''],
                ['UTILIDAD NETA', utilidad_neta],
            ]
            
            df_estado = pd.DataFrame(estado_resultados_data, columns=['Concepto', 'Valor'])
            df_estado.to_excel(writer, sheet_name='Estado de Resultados', index=False)
            
            worksheet = writer.sheets['Estado de Resultados']
            # Aplicar zoom para mejor visibilidad
            worksheet.set_zoom(110)
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 25)
            # Congelar primera fila y primera columna
            worksheet.freeze_panes(1, 1)
            
            # Aplicar formato monetario
            for row in [5, 6, 9, 10, 12, 16, 17, 19]:
                if row < len(estado_resultados_data) and len(estado_resultados_data[row]) > 1:
                    worksheet.write(row, 1, estado_resultados_data[row][1], money_format)
            
            # 3. HOJA: BALANCE GENERAL
            balance_data = [
                ['BALANCE GENERAL', ''],
                ['Empresa', empresa.nombre],
                ['Fecha', datetime.now().strftime('%d/%m/%Y')],
                ['', ''],
                ['ACTIVOS', ''],
            ]
            
            for activo in activos:
                balance_data.append([activo['cuenta_fk__nombre'], activo['valor']])
            
            balance_data.extend([
                ['Total Activos', total_activos],
                ['', ''],
                ['PASIVOS', ''],
            ])
            
            for pasivo in pasivos:
                balance_data.append([pasivo['cuenta_fk__nombre'], pasivo['valor']])
            
            balance_data.extend([
                ['Total Pasivos', total_pasivos],
                ['', ''],
                ['PATRIMONIO', ''],
            ])
            
            for cap in capital:
                balance_data.append([cap['cuenta_fk__nombre'], cap['valor']])
            
            balance_data.extend([
                ['Total Patrimonio', total_patrimonio],
                ['', ''],
                ['ECUACIÓN CONTABLE', ''],
                ['Activos = Pasivos + Patrimonio', f'{total_activos} = {total_pasivos} + {total_patrimonio}'],
            ])
            
            df_balance = pd.DataFrame(balance_data, columns=['Concepto', 'Valor'])
            df_balance.to_excel(writer, sheet_name='Balance General', index=False)
            
            worksheet = writer.sheets['Balance General']
            worksheet.set_column('A:A', 35)
            worksheet.set_column('B:B', 25)
            
            # Aplicar formato monetario
            for row in range(len(balance_data)):
                if isinstance(balance_data[row][1], (int, float)) and balance_data[row][1] != '':
                    worksheet.write(row, 1, balance_data[row][1], money_format)
            
            # 4. HOJA: FLUJO DE CAJA
            if flujo_mensual:
                df_flujo = pd.DataFrame(flujo_mensual)
                df_flujo.to_excel(writer, sheet_name='Flujo de Caja', index=False)
                
                worksheet = writer.sheets['Flujo de Caja']
                worksheet.set_column('A:A', 15)
                worksheet.set_column('B:D', 20, money_format)
                
                # Aplicar formato de encabezados
                for col_num, value in enumerate(df_flujo.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                worksheet.freeze_panes(1, 0)
                worksheet.autofilter(0, 0, len(df_flujo), len(df_flujo.columns)-1)
            
            # 5. HOJA: VENTAS
            if ventas.exists():
                ventas_data = list(ventas.values(
                    'fecha', 'producto__nombre', 'cliente', 'cantidad', 'precio_unitario', 'total'
                ))
                df_ventas = pd.DataFrame(ventas_data)
                # Convertir fechas a timezone-naive
                if 'fecha' in df_ventas.columns:
                    df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha']).dt.tz_localize(None)
                df_ventas.rename(columns={
                    'fecha': 'Fecha', 'producto__nombre': 'Producto', 'cliente': 'Cliente',
                    'cantidad': 'Cantidad', 'precio_unitario': 'Precio Unitario', 'total': 'Total'
                }, inplace=True)
                
                df_ventas.to_excel(writer, sheet_name='Ventas', index=False)
                worksheet = writer.sheets['Ventas']
                worksheet.set_column('A:A', 18, date_format)
                worksheet.set_column('B:B', 25)
                worksheet.set_column('C:C', 20)
                worksheet.set_column('D:D', 12)
                worksheet.set_column('E:F', 15, money_format)
                
                # Aplicar formato de encabezados
                for col_num, value in enumerate(df_ventas.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                worksheet.freeze_panes(1, 0)
                worksheet.autofilter(0, 0, len(df_ventas), len(df_ventas.columns)-1)
            
            # 6. HOJA: COMPRAS
            if compras.exists():
                compras_data = list(compras.values(
                    'fecha', 'producto__nombre', 'proveedor', 'cantidad', 'total'
                ))
                df_compras = pd.DataFrame(compras_data)
                # Convertir fechas a timezone-naive
                if 'fecha' in df_compras.columns:
                    df_compras['fecha'] = pd.to_datetime(df_compras['fecha']).dt.tz_localize(None)
                df_compras['precio_unitario'] = df_compras.apply(
                    lambda row: row['total'] / row['cantidad'] if row['cantidad'] > 0 else 0, axis=1
                )
                df_compras.rename(columns={
                    'fecha': 'Fecha', 'producto__nombre': 'Producto', 'proveedor': 'Proveedor',
                    'cantidad': 'Cantidad', 'precio_unitario': 'Precio Unitario', 'total': 'Total'
                }, inplace=True)
                
                df_compras.to_excel(writer, sheet_name='Compras', index=False)
                worksheet = writer.sheets['Compras']
                worksheet.set_column('A:A', 18, date_format)
                worksheet.set_column('B:B', 25)
                worksheet.set_column('C:C', 20)
                worksheet.set_column('D:D', 12)
                worksheet.set_column('E:F', 15, money_format)
                
                # Aplicar formato de encabezados
                for col_num, value in enumerate(df_compras.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                worksheet.freeze_panes(1, 0)
                worksheet.autofilter(0, 0, len(df_compras), len(df_compras.columns)-1)
            
            # 7. HOJA: GASTOS
            if gastos.exists():
                gastos_data = list(gastos.values('fecha', 'descripcion', 'categoria', 'monto'))
                df_gastos = pd.DataFrame(gastos_data)
                # Convertir fechas a timezone-naive
                if 'fecha' in df_gastos.columns:
                    df_gastos['fecha'] = pd.to_datetime(df_gastos['fecha']).dt.tz_localize(None)
                df_gastos.rename(columns={
                    'fecha': 'Fecha', 'descripcion': 'Concepto', 'categoria': 'Categoría', 'monto': 'Monto'
                }, inplace=True)
                
                df_gastos.to_excel(writer, sheet_name='Gastos', index=False)
                worksheet = writer.sheets['Gastos']
                worksheet.set_column('A:A', 18, date_format)
                worksheet.set_column('B:B', 30)
                worksheet.set_column('C:C', 20)
                worksheet.set_column('D:D', 15, money_format)
                
                # Aplicar formato de encabezados
                for col_num, value in enumerate(df_gastos.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                worksheet.freeze_panes(1, 0)
                worksheet.autofilter(0, 0, len(df_gastos), len(df_gastos.columns)-1)
            
            # 8. HOJA: INVENTARIO
            if productos.exists():
                inventario_data = []
                for producto in productos:
                    valor_total = producto.stock * (producto.precio_unitario or 0)
                    inventario_data.append({
                        'Código': producto.codigo,
                        'Nombre': producto.nombre,
                        'Descripción': producto.descripcion or '',
                        'Stock Actual': producto.stock,
                        'Precio Unitario': producto.precio_unitario or 0,
                        'Precio de Venta (PVP)': producto.pvp or 0,
                        'Valor Total': valor_total,
                        'Estado': 'Alto Stock' if producto.stock > 20 else 'Stock Medio' if producto.stock > 10 else 'Bajo Stock' if producto.stock > 0 else 'Agotado'
                    })
                
                df_inventario = pd.DataFrame(inventario_data)
                df_inventario.to_excel(writer, sheet_name='Inventario', index=False)
                worksheet = writer.sheets['Inventario']
                worksheet.set_column('A:A', 15)
                worksheet.set_column('B:B', 25)
                worksheet.set_column('C:C', 30)
                worksheet.set_column('D:D', 12)
                worksheet.set_column('E:F', 18, money_format)
                worksheet.set_column('G:G', 15, money_format)
                worksheet.set_column('H:H', 15)
                
                # Aplicar formato de encabezados
                for col_num, value in enumerate(df_inventario.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                worksheet.freeze_panes(1, 0)
                worksheet.autofilter(0, 0, len(df_inventario), len(df_inventario.columns)-1)
            
            # 9. HOJA: ANÁLISIS MENSUAL
            if ventas.exists():
                ventas_mensuales = []
                for venta in ventas:
                    ventas_mensuales.append({
                        'Mes': venta.fecha.strftime('%B %Y'),
                        'Año': venta.fecha.year,
                        'Mes_Num': venta.fecha.month,
                        'Total': venta.total
                    })
                
                if ventas_mensuales:
                    df_ventas_mensual = pd.DataFrame(ventas_mensuales)
                    if len(df_ventas_mensual) > 0:
                        df_ventas_mensual = df_ventas_mensual.groupby(['Mes', 'Año', 'Mes_Num']).agg({
                            'Total': 'sum'
                        }).reset_index().sort_values(['Año', 'Mes_Num'])
                        
                        df_ventas_mensual = df_ventas_mensual[['Mes', 'Total']]
                        df_ventas_mensual.to_excel(writer, sheet_name='Análisis Mensual', index=False)
                        
                        worksheet = writer.sheets['Análisis Mensual']
                        worksheet.set_column('A:A', 20)
                        worksheet.set_column('B:B', 15, money_format)
                        
                        # Aplicar formato de encabezados
                        for col_num, value in enumerate(df_ventas_mensual.columns.values):
                            worksheet.write(0, col_num, value, header_format)
                        worksheet.freeze_panes(1, 0)
                        worksheet.autofilter(0, 0, len(df_ventas_mensual), len(df_ventas_mensual.columns)-1)
            
            # 10. HOJA: TOP PRODUCTOS
            if ventas.exists():
                ventas_data = list(ventas.values('producto__nombre', 'cantidad', 'total'))
                if ventas_data:
                    df_top_productos = pd.DataFrame(ventas_data)
                    df_top_productos = df_top_productos.groupby('producto__nombre').agg({
                        'cantidad': 'sum',
                        'total': 'sum'
                    }).reset_index()
                    df_top_productos = df_top_productos.sort_values('total', ascending=False)
                    df_top_productos.rename(columns={
                        'producto__nombre': 'Producto',
                        'cantidad': 'Cantidad Vendida',
                        'total': 'Total Ventas'
                    }, inplace=True)
                    
                    df_top_productos.to_excel(writer, sheet_name='Top Productos', index=False)
                    worksheet = writer.sheets['Top Productos']
                    worksheet.set_column('A:A', 25)
                    worksheet.set_column('B:B', 15)
                    worksheet.set_column('C:C', 15, money_format)
                    
                    # Aplicar formato de encabezados
                    for col_num, value in enumerate(df_top_productos.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    worksheet.freeze_panes(1, 0)
                    worksheet.autofilter(0, 0, len(df_top_productos), len(df_top_productos.columns)-1)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        fecha_str = datetime.now().strftime("%Y%m%d")
        response['Content-Disposition'] = f'attachment; filename="reporte_completo_{empresa.nombre}_{fecha_str}.xlsx"'
        return response
        
    except IndexError as e:
        print(f"Error de índice en exportar_excel_completo: {e}")
        return HttpResponse(f"Error al exportar Excel completo: Error de índice - {str(e)}", status=500)
    except Exception as e:
        print(f"Error general en exportar_excel_completo: {e}")
        return HttpResponse(f"Error al exportar Excel completo: {str(e)}", status=500)

@login_required
def exportar_excel_iva(request):
    """Exporta reporte de IVA a Excel"""
    try:
        empresa = request.user.empresa
        mes = int(request.GET.get('mes', datetime.now().month))
        anio = int(request.GET.get('anio', datetime.now().year))
        
        # IVA por pagar (ventas)
        ventas_iva = Venta.objects.filter(
            empresa=empresa,
            fecha__month=mes,
            fecha__year=anio
        ).values('fecha', 'producto__nombre', 'cliente_display', 'monto_neto', 'iva', 'monto')
        
        # IVA crédito fiscal (compras)
        compras_iva = Compra.objects.filter(
            empresa=empresa,
            fecha__month=mes,
            fecha__year=anio
        ).values('fecha', 'producto__nombre', 'proveedor_display', 'monto_neto', 'iva', 'monto')
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Formato de encabezados
            header_format = workbook.add_format({
                'bold': True, 'bg_color': '#1976d2', 'font_color': 'white',
                'border': 1, 'align': 'center', 'font_size': 12
            })
            
            money_format = workbook.add_format({
                'num_format': '$#,##0.00', 'border': 1, 'align': 'center'
            })
            
            # Hoja de IVA Ventas
            if ventas_iva:
                df_ventas = pd.DataFrame(list(ventas_iva))
                df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha']).dt.strftime('%d/%m/%Y')
                df_ventas.rename(columns={
                    'fecha': 'Fecha',
                    'producto__nombre': 'Producto',
                    'cliente_display': 'Cliente',
                    'monto_neto': 'Base Imponible',
                    'iva': 'IVA',
                    'monto': 'Total'
                }, inplace=True)
                
                df_ventas.to_excel(writer, sheet_name='IVA Ventas', index=False)
                worksheet = writer.sheets['IVA Ventas']
                
                for col_num, value in enumerate(df_ventas.columns):
                    worksheet.write(0, col_num, value, header_format)
                    if col_num >= 3:  # Columnas monetarias
                        worksheet.set_column(col_num, col_num, 15, money_format)
                    else:
                        worksheet.set_column(col_num, col_num, 20)
            
            # Hoja de IVA Compras
            if compras_iva:
                df_compras = pd.DataFrame(list(compras_iva))
                df_compras['fecha'] = pd.to_datetime(df_compras['fecha']).dt.strftime('%d/%m/%Y')
                df_compras.rename(columns={
                    'fecha': 'Fecha',
                    'producto__nombre': 'Producto',
                    'proveedor_display': 'Proveedor',
                    'monto_neto': 'Base Imponible',
                    'iva': 'IVA',
                    'monto': 'Total'
                }, inplace=True)
                
                df_compras.to_excel(writer, sheet_name='IVA Compras', index=False)
                worksheet = writer.sheets['IVA Compras']
                
                for col_num, value in enumerate(df_compras.columns):
                    worksheet.write(0, col_num, value, header_format)
                    if col_num >= 3:  # Columnas monetarias
                        worksheet.set_column(col_num, col_num, 15, money_format)
                    else:
                        worksheet.set_column(col_num, col_num, 20)
            
            # Hoja de Resumen
            total_iva_ventas = sum(v['iva'] for v in ventas_iva) if ventas_iva else 0
            total_iva_compras = sum(c['iva'] for c in compras_iva) if compras_iva else 0
            iva_a_pagar = total_iva_ventas - total_iva_compras
            
            resumen_data = [
                ['RESUMEN IVA', ''],
                ['Período', f'{mes:02d}/{anio}'],
                ['', ''],
                ['IVA por Pagar (Ventas)', total_iva_ventas],
                ['IVA Crédito Fiscal (Compras)', total_iva_compras],
                ['IVA Neto a Pagar', iva_a_pagar],
            ]
            
            df_resumen = pd.DataFrame(resumen_data, columns=['Concepto', 'Valor'])
            df_resumen.to_excel(writer, sheet_name='Resumen IVA', index=False)
            
            worksheet = writer.sheets['Resumen IVA']
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 20)
            
            for row in [3, 4, 5]:  # Filas con valores monetarios
                worksheet.write(row, 1, resumen_data[row][1], money_format)
        
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="reporte_iva_{mes:02d}_{anio}_{empresa.nombre}.xlsx"'
        return response
        
    except Exception as e:
        return HttpResponse(f"Error al exportar IVA: {str(e)}", status=500)

@login_required
def exportar_pdf_iva(request):
    """Exporta reporte de IVA a PDF"""
    try:
        empresa = request.user.empresa
        mes = int(request.GET.get('mes', datetime.now().month))
        anio = int(request.GET.get('anio', datetime.now().year))
        
        # Calcular totales de IVA
        total_iva_ventas = Venta.objects.filter(
            empresa=empresa, fecha__month=mes, fecha__year=anio
        ).aggregate(total=Sum('iva'))['total'] or 0
        
        total_iva_compras = Compra.objects.filter(
            empresa=empresa, fecha__month=mes, fecha__year=anio
        ).aggregate(total=Sum('iva'))['total'] or 0
        
        iva_a_pagar = total_iva_ventas - total_iva_compras
        
        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=20, spaceAfter=30, alignment=TA_CENTER, textColor=colors.darkblue
        )
        
        # Título
        story.append(Paragraph(f"REPORTE DE IVA - {empresa.nombre.upper()}", title_style))
        story.append(Paragraph(f"Período: {mes:02d}/{anio}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Tabla de resumen
        data = [
            ['Concepto', 'Valor'],
            ['IVA por Pagar (Ventas)', f'${total_iva_ventas:,.2f}'],
            ['IVA Crédito Fiscal (Compras)', f'${total_iva_compras:,.2f}'],
            ['IVA Neto a Pagar', f'${iva_a_pagar:,.2f}']
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Información adicional
        story.append(Paragraph("INFORMACIÓN ADICIONAL", styles['Heading2']))
        story.append(Paragraph(f"• Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"• Sistema: CONTAFY - Plataforma de Gestión para PYMES", styles['Normal']))
        
        if iva_a_pagar > 0:
            story.append(Paragraph(f"• Debe pagar IVA por: ${iva_a_pagar:,.2f}", styles['Normal']))
        elif iva_a_pagar < 0:
            story.append(Paragraph(f"• Tiene saldo a favor de: ${abs(iva_a_pagar):,.2f}", styles['Normal']))
        else:
            story.append(Paragraph("• No tiene IVA por pagar este período", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_iva_{mes:02d}_{anio}_{empresa.nombre}.pdf"'
        return response
        
    except Exception as e:
        return HttpResponse(f"Error al exportar PDF IVA: {str(e)}", status=500)
