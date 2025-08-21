from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from empresa.models import Producto
from empresa.forms import ProductoForm
from empresa.decorators import require_power
from django.contrib import messages
import requests


@login_required
@require_power('puede_editar_productos')
def crear_producto(request):
    empresa = request.user.empresa

    if request.method == 'POST':
        form = ProductoForm(request.POST, empresa=empresa)
        if form.is_valid():
            from django.db import transaction
            from empresa.views.contabilidad import registrar_movimiento_contable
            
            try:
                with transaction.atomic():
                    producto = form.save()
                    
                    # REGISTRAR COMPRA INICIAL SI HAY STOCK
                    if producto.stock > 0 and producto.precio_unitario > 0:
                        costo_total = producto.stock * producto.precio_unitario
                        
                        # Registrar movimiento contable: Débito Inventario + Crédito Capital
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Inventario',
                            cuenta_credito_nombre='Capital',
                            monto=costo_total,
                            descripcion=f"Inventario inicial: {producto.nombre} (x{producto.stock})",
                            tipo_cuenta_debito='activo',
                            tipo_cuenta_credito='capital'
                        )
                        
                        messages.success(request, f'Producto creado e inventario inicial registrado: ${costo_total:,.2f}')
                    else:
                        messages.success(request, 'Producto creado correctamente')
                        
            except Exception as e:
                messages.error(request, f'Error creando producto: {e}')
                return render(request, 'empresa/crear_producto.html', {'form': form})
                
            return redirect('empresa:home')
    else:
        form = ProductoForm(empresa=empresa)

    return render(request, 'empresa/crear_producto.html', {'form': form})


@login_required
@require_power('puede_gestionar_inventario')
def listar_productos(request):
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
            Q(descripcion__icontains=buscar) |
            Q(codigo_barras__icontains=buscar)
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
    total_inventario = sum(p.stock * float(p.precio_unitario) for p in productos)
    total_pvp = sum(p.stock * float(p.pvp or 0) for p in productos)
    productos_bajo_stock = productos.filter(stock__lte=10).count()
    
    context = {
        'productos': productos,
        'total_inventario': total_inventario,
        'total_pvp': total_pvp,
        'productos_bajo_stock': productos_bajo_stock,
    }
    
    return render(request, 'empresa/listar_productos.html', context)


@login_required
def obtener_info_producto(request):
    # Esta función puede quedar como compatibilidad, pero la búsqueda principal es en info_producto_api
    return JsonResponse({'error': 'Usa el endpoint principal de info_producto_api'}, status=404)


@login_required
def info_producto_api(request):
    codigo = request.GET.get('codigo', '')
    empresa = request.user.empresa
    
    # 1. Consultar API global (Open Food Facts)
    api_url = f'https://world.openfoodfacts.org/api/v0/product/{codigo}.json'
    try:
        # En modo sandbox evitamos consultas externas y devolvemos None para
        # que la b\u00fasqueda local se ejecute. Esto previene llamadas a servicios
        # externos durante simulaciones.
        from empresa.sandbox_mode import is_sandbox
        if is_sandbox():
            # Simular no encontrado en API externa cuando est\u00e1 en sandbox
            raise RuntimeError('Sandbox mode - skipping external API call')

        r = requests.get(api_url, timeout=4)
        if r.status_code == 200:
            data = r.json()
            if data.get('status') == 1:
                producto = data['product']
                nombre = producto.get('product_name', '')
                descripcion = producto.get('generic_name', '')
                if not descripcion:
                    descripcion = producto.get('categories', '')
                if not descripcion:
                    descripcion = producto.get('brands', '')
                if not descripcion:
                    descripcion = f"Producto: {nombre}"
                precio = ''
                return JsonResponse({
                    'nombre': nombre,
                    'descripcion': descripcion,
                    'categoria': producto.get('categories', '').split(',')[0] if producto.get('categories') else '',
                    'precio_unitario': precio,
                    'mensaje_precio': 'No se encontr\u00f3 precio autom\u00e1tico. Por favor, ingr\u00e9salo en USD.',
                    'fuente': 'api_global',
                })
    except Exception:
        # Silenciar errores y permitir la b\u00fasqueda local
        pass
    
    # 2. Si no se encuentra, buscar localmente SOLO en la empresa del usuario
    producto = Producto.objects.filter(codigo=codigo, empresa=empresa).first()
    if producto:
        return JsonResponse({
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'categoria': 'General',
            'precio_unitario': float(producto.precio_unitario),
            'mensaje_precio': '',
            'fuente': 'local',
        })
    
    # 3. No encontrado
    return JsonResponse({'error': 'No encontrado'}, status=404)


@login_required
@require_power('puede_editar_productos')
def editar_producto(request, producto_id):
    empresa = request.user.empresa
    try:
        producto = Producto.objects.get(id=producto_id, empresa=empresa)
    except Producto.DoesNotExist:
        messages.error(request, 'Producto no encontrado o no pertenece a tu empresa.')
        return redirect('empresa:listar_productos')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, empresa=empresa, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('empresa:home')
    else:
        form = ProductoForm(empresa=empresa, instance=producto)
    
    return render(request, 'empresa/crear_producto.html', {'form': form, 'producto': producto})


@login_required
def eliminar_producto(request, producto_id):
    empresa = request.user.empresa
    try:
        producto = Producto.objects.get(id=producto_id, empresa=empresa)
        producto.delete()
        messages.success(request, 'Producto eliminado correctamente.')
    except Producto.DoesNotExist:
        messages.error(request, 'Producto no encontrado o no pertenece a tu empresa.')
    
    return redirect('empresa:listar_productos')
