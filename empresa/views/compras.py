# empresa/views/compras.py

import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from empresa.models import Compra, Producto
from empresa.forms import CompraForm
from empresa.views.contabilidad import registrar_movimiento_contable
from django.db import transaction
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q

@login_required
def crear_compra(request):
    empresa = request.user.empresa

    if request.method == 'POST':
        form = CompraForm(request.POST, empresa=empresa)
        if form.is_valid():
            try:
                with transaction.atomic():
                    compra = form.save(commit=False)
                    compra.empresa = empresa
                    compra.creado_por = request.user
                    compra.save()  # El modelo se encarga automáticamente de crear la cuenta por pagar
                    
                    # Actualizar stock del producto
                    producto = compra.producto
                    producto.stock += compra.cantidad
                    producto.save()
                    # Registrar compra según tipo de pago
                    if compra.tipo_pago == 'contado':
                        cuenta_credito = 'Caja/Banco'
                    else:
                        cuenta_credito = 'Cuentas por Pagar'
                    
                    registrar_movimiento_contable(
                        empresa=empresa,
                        cuenta_debito_nombre='Inventario',
                        cuenta_credito_nombre=cuenta_credito,
                        monto=compra.monto,
                        descripcion=f"Compra de {compra.producto.nombre} (x{compra.cantidad}) - {compra.get_tipo_pago_display()}",
                        tipo_cuenta_debito='activo',
                        tipo_cuenta_credito='activo' if compra.tipo_pago == 'contado' else 'pasivo'
                    )
                messages.success(request, 'Compra registrada correctamente.')
                return redirect('empresa:home')
            except Exception as e:
                messages.error(request, f'Error al registrar compra: {e}')
    else:
        form = CompraForm(empresa=empresa)

    # Preparar JSON de productos para el JS
    productos = Producto.objects.filter(empresa=empresa).values(
        'id', 'codigo', 'codigo_barras', 'nombre', 'precio_unitario', 'stock'
    )
    # Helper para convertir Decimals a float
    from decimal import Decimal
    def decimal_to_float(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, dict):
            return {k: decimal_to_float(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [decimal_to_float(i) for i in obj]
        return obj
    productos_list = []
    for p in productos:
        productos_list.append({
            'id': p['id'],
            'codigo': p['codigo'],
            'codigo_barras': p['codigo_barras'] or '',
            'nombre': p['nombre'],
            'precio_unitario': float(p['precio_unitario']),
            'stock': p['stock']
        })
    productos_json = json.dumps(productos_list)

    return render(request, 'empresa/crear_compra.html', {
        'form': form,
        'productos_json': productos_json,
    })


@login_required
def listar_compras(request):
    empresa = request.user.empresa
    compras = Compra.objects.filter(empresa=empresa).order_by('-fecha')

    # Filtros avanzados
    buscar = request.GET.get('buscar', '').strip()
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    monto = request.GET.get('monto')

    if buscar:
        compras = compras.filter(
            Q(producto__nombre__icontains=buscar) |
            Q(producto__codigo__icontains=buscar) |
            Q(proveedor__icontains=buscar)
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

    # Estadísticas generales
    total_compras = compras.aggregate(total=Sum('monto'))['total'] or 0
    total_transacciones = compras.count()
    promedio_compra = compras.aggregate(promedio=Avg('monto'))['promedio'] or 0

    contexto = {
        'compras': compras,
        'total_compras': total_compras,
        'total_transacciones': total_transacciones,
        'promedio_compra': promedio_compra,
    }
    return render(request, 'empresa/listar_compra.html', contexto)
