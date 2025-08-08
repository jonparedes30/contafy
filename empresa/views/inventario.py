from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
import pandas as pd
import openpyxl
import io
from django.contrib import messages
from empresa.models import Producto
from django.contrib.auth.decorators import login_required
from empresa.forms import SaldosInicialesForm
from empresa.views.contabilidad import registrar_movimiento_contable
from django.utils import timezone
from datetime import datetime

@login_required
def inventario(request):
    empresa = request.user.empresa
    
    # Obtener parámetros de filtro
    buscar = request.GET.get('buscar', '')
    categoria_id = request.GET.get('categoria', '')
    stock_filter = request.GET.get('stock', '')
    
    # Filtrar productos
    productos = Producto.objects.filter(empresa=empresa)
    
    if buscar:
        productos = productos.filter(
            Q(codigo__icontains=buscar) |
            Q(nombre__icontains=buscar) |
            Q(descripcion__icontains=buscar)
        )
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
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
    total_pvp = sum(p.stock * (p.pvp or 0) for p in productos)
    
    # Por ahora no hay categorías de productos, usar lista vacía
    categorias = []
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(productos, 25)  # 25 productos por página
    page_number = request.GET.get('page')
    productos_paginados = paginator.get_page(page_number)
    
    return render(request, 'empresa/inventario.html', {
        'productos': productos_paginados,
        'total_productos': total_productos,
        'productos_bajo_stock': productos_bajo_stock,
        'total_inventario': total_inventario,
        'total_pvp': total_pvp,
        'categorias': categorias,
    })

@login_required
def descargar_plantilla_inventario(request):
    # Crear un DataFrame con todos los campos del modelo Producto
    df = pd.DataFrame(columns=[
        'codigo', 'codigo_barras', 'nombre', 'descripcion', 'precio_unitario', 'pvp', 
        'stock', 'stock_minimo', 'stock_maximo', 'fecha_vencimiento', 'lote'
    ])
    
    # Agregar fila de ejemplo
    ejemplo = {
        'codigo': 'PROD001',
        'codigo_barras': '1234567890123',
        'nombre': 'Producto Ejemplo',
        'descripcion': 'Descripción del producto',
        'precio_unitario': 10.50,
        'pvp': 15.75,
        'stock': 100,
        'stock_minimo': 10,
        'stock_maximo': 500,
        'fecha_vencimiento': '2025-12-31',
        'lote': 'L001'
    }
    df = pd.DataFrame([ejemplo])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
        
        # Agregar comentarios en las celdas
        worksheet = writer.sheets['Inventario']
        worksheet['A1'].comment = 'Código único del producto (obligatorio)'
        worksheet['B1'].comment = 'Código de barras (opcional)'
        worksheet['C1'].comment = 'Nombre del producto (obligatorio)'
        worksheet['D1'].comment = 'Descripción detallada (opcional)'
        worksheet['E1'].comment = 'Precio de costo/compra'
        worksheet['F1'].comment = 'Precio de venta al público'
        worksheet['G1'].comment = 'Cantidad en stock'
        worksheet['H1'].comment = 'Stock mínimo para alertas'
        worksheet['I1'].comment = 'Stock máximo recomendado'
        worksheet['J1'].comment = 'Fecha de vencimiento (YYYY-MM-DD)'
        worksheet['K1'].comment = 'Número de lote'
    
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=plantilla_inventario_completa.xlsx'
    return response

@login_required
def subir_inventario_excel(request):
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        try:
            df = pd.read_excel(archivo)
        except Exception as e:
            messages.error(request, f'Error al leer el archivo: {e}')
            return render(request, 'empresa/subir_inventario.html')
        
        # Validar columnas obligatorias
        columnas_obligatorias = {'codigo', 'nombre'}
        if not columnas_obligatorias.issubset(set(df.columns)):
            messages.error(request, 'La plantilla debe tener al menos las columnas: codigo, nombre')
            return render(request, 'empresa/subir_inventario.html')
        
        empresa = request.user.empresa
        creados, actualizados, errores = 0, 0, 0
        
        for index, row in df.iterrows():
            try:
                # Preparar datos con valores por defecto
                datos = {
                    'nombre': str(row['nombre']).strip(),
                    'descripcion': str(row.get('descripcion', '')).strip(),
                    'precio_unitario': float(row.get('precio_unitario', 0) or 0),
                    'pvp': float(row.get('pvp', 0) or 0),
                    'stock': int(row.get('stock', 0) or 0),
                    'stock_minimo': int(row.get('stock_minimo', 5) or 5),
                    'stock_maximo': int(row.get('stock_maximo', 0) or 0) if row.get('stock_maximo') else None,
                    'codigo_barras': str(row.get('codigo_barras', '')).strip() if row.get('codigo_barras') else None,
                    'lote': str(row.get('lote', '')).strip() if row.get('lote') else '',
                }
                
                # Manejar fecha de vencimiento
                if row.get('fecha_vencimiento'):
                    try:
                        from datetime import datetime
                        if isinstance(row['fecha_vencimiento'], str):
                            datos['fecha_vencimiento'] = datetime.strptime(row['fecha_vencimiento'], '%Y-%m-%d').date()
                        else:
                            datos['fecha_vencimiento'] = row['fecha_vencimiento']
                    except:
                        datos['fecha_vencimiento'] = None
                else:
                    datos['fecha_vencimiento'] = None
                
                # Crear o actualizar producto
                prod, creado = Producto.objects.update_or_create(
                    empresa=empresa,
                    codigo=str(row['codigo']).strip().upper(),
                    defaults=datos
                )
                
                if creado:
                    creados += 1
                else:
                    actualizados += 1
                    
            except Exception as e:
                errores += 1
                print(f'Error en fila {index + 2}: {e}')
        
        if errores > 0:
            messages.warning(request, f'Inventario cargado con {errores} errores: {creados} productos creados, {actualizados} actualizados.')
        else:
            messages.success(request, f'Inventario cargado exitosamente: {creados} productos creados, {actualizados} actualizados.')
        
        return render(request, 'empresa/subir_inventario.html', {
            'exito': True, 
            'creados': creados, 
            'actualizados': actualizados,
            'errores': errores
        })
    
    return render(request, 'empresa/subir_inventario.html')

@login_required
def saldos_iniciales(request):
    empresa = request.user.empresa
    
    if request.method == 'POST':
        form = SaldosInicialesForm(request.POST, empresa=empresa)
        if form.is_valid():
            caja = form.cleaned_data['caja_banco'] or 0
            inventario_global = form.cleaned_data['inventario_global'] or 0
            usar_inventario_detallado = form.cleaned_data['usar_inventario_detallado']
            
            total_activo = caja + inventario_global
            capital = total_activo  # Capital social como contrapartida
            
            # Registrar movimientos contables de partida doble
            if caja > 0:
                registrar_movimiento_contable(
                    empresa=empresa,
                    cuenta_debito_nombre='Caja/Banco',
                    cuenta_credito_nombre='Capital Social',
                    monto=caja,
                    descripcion='Saldo inicial de Caja/Banco'
                )
            
            # OPCIÓN 1: Inventario Global
            if inventario_global > 0:
                # Crear producto "Inventario Inicial" si no existe
                producto_inventario, created = Producto.objects.get_or_create(
                    empresa=empresa,
                    nombre='Inventario Inicial',
                    defaults={
                        'codigo': 'INV-INICIAL',
                        'precio_unitario': inventario_global,
                        'pvp': inventario_global,
                        'stock': 1,  # 1 unidad con el valor total
                        'descripcion': 'Producto que representa el inventario inicial de la empresa'
                    }
                )
                
                if not created:
                    # Si ya existe, actualizar el stock
                    producto_inventario.stock = 1
                    producto_inventario.precio_unitario = inventario_global
                    producto_inventario.pvp = inventario_global
                    producto_inventario.save()
                
                # Registrar movimiento contable
                registrar_movimiento_contable(
                    empresa=empresa,
                    cuenta_debito_nombre='Inventario',
                    cuenta_credito_nombre='Capital Social',
                    monto=inventario_global,
                    descripcion='Saldo inicial de Inventario (Global)'
                )
            
            # OPCIÓN 2: Inventario Detallado por Producto
            if usar_inventario_detallado:
                # Redirigir a una vista para registrar inventario por producto
                return redirect('inventario_detallado_inicial')
            
            return render(request, 'empresa/saldos_iniciales.html', {
                'form': form, 
                'exito': True, 
                'caja': caja, 
                'inventario': inventario_global, 
                'capital': capital,
                'usar_inventario_detallado': usar_inventario_detallado
            })
    else:
        form = SaldosInicialesForm(empresa=empresa)
    
    return render(request, 'empresa/saldos_iniciales.html', {'form': form})


@login_required
def inventario_detallado_inicial(request):
    """Vista para registrar inventario inicial por producto individual"""
    empresa = request.user.empresa
    productos = Producto.objects.filter(empresa=empresa)
    
    if request.method == 'POST':
        # Procesar formularios de inventario detallado
        total_inventario = 0
        
        for producto in productos:
            cantidad_key = f'cantidad_{producto.id}'
            precio_key = f'precio_{producto.id}'
            
            cantidad = request.POST.get(cantidad_key)
            precio = request.POST.get(precio_key)
            
            if cantidad and precio and float(cantidad) > 0 and float(precio) > 0:
                cantidad = int(cantidad)
                precio = float(precio)
                
                # Actualizar stock del producto
                producto.stock = cantidad
                producto.precio_unitario = precio
                producto.save()
                
                total_inventario += cantidad * precio
        
        # Registrar movimiento contable del inventario detallado
        if total_inventario > 0:
            registrar_movimiento_contable(
                empresa=empresa,
                cuenta_debito_nombre='Inventario',
                cuenta_credito_nombre='Capital Social',
                monto=total_inventario,
                descripcion='Saldo inicial de Inventario (Detallado por producto)'
            )
        
        messages.success(request, f'✅ Inventario inicial detallado registrado: ${total_inventario:,.2f}')
        return redirect('inventario')
    
    return render(request, 'empresa/inventario_detallado_inicial.html', {
        'productos': productos
    }) 