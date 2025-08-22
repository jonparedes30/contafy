# empresa/views/ventas.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from empresa.models import Venta, Producto
from empresa.forms import VentaForm
from empresa.decorators import require_power
from empresa.views.contabilidad import registrar_movimiento_contable
from django.db import transaction
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q
from datetime import datetime, timedelta
from django.utils import timezone

@login_required
@require_power('puede_registrar_ventas')
def crear_venta(request):
    empresa = request.user.empresa
    
    # Detectar si es empresa de servicios y cargar servicios
    servicios = []
    if empresa.categoria == 'servicios':
        from empresa.models import TipoServicio
        servicios_queryset = TipoServicio.objects.filter(empresa=empresa, activo=True)
        servicios = [{
            'id': s.id,
            'nombre': s.nombre,
            'precio_base': float(s.precio_base),
            'costo_directo': float(s.costo_directo),
            'unidad_medida': s.unidad_medida
        } for s in servicios_queryset]

    if request.method == 'POST':
        # Manejar venta de servicio
        if empresa.categoria == 'servicios' and request.POST.get('servicio_id'):
            return procesar_venta_servicio(request, empresa)
        # Manejar venta de producto normal
        form = VentaForm(request.POST, empresa=empresa)
        if form.is_valid():
            try:
                with transaction.atomic():
                    venta = form.save(commit=False)
                    venta.empresa = empresa
                    venta.creado_por = request.user
                    venta.save()
                    
                    # Crear cuenta por cobrar si es crédito
                    if venta.tipo_pago == 'credito' and venta.cliente_fk:
                        from empresa.models import CuentaPorCobrar
                        from datetime import date, timedelta
                        CuentaPorCobrar.objects.create(
                            empresa=venta.empresa,
                            cliente=venta.cliente_fk,
                            venta=venta,
                            monto_original=venta.monto,
                            monto_pendiente=venta.monto,
                            fecha_vencimiento=date.today() + timedelta(days=30)
                        )
                    
                    # Actualizar stock del producto
                    producto = venta.producto
                    producto.stock -= venta.cantidad
                    producto.save()
                    # 1. Registrar la venta según tipo de pago
                    if venta.tipo_pago == 'contado':
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Caja',
                            cuenta_credito_nombre='Ventas',
                            monto=venta.monto,
                            descripcion=f"Venta contado {venta.producto.nombre} (x{venta.cantidad})",
                            tipo_cuenta_debito='activo',
                            tipo_cuenta_credito='ingreso'
                        )
                    elif venta.tipo_pago == 'transferencia':
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Banco',
                            cuenta_credito_nombre='Ventas',
                            monto=venta.monto,
                            descripcion=f"Venta transferencia {venta.producto.nombre} (x{venta.cantidad})",
                            tipo_cuenta_debito='activo',
                            tipo_cuenta_credito='ingreso'
                        )
                    elif venta.tipo_pago == 'tarjeta':
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Cuentas por Cobrar - Tarjetas',
                            cuenta_credito_nombre='Ventas',
                            monto=venta.monto,
                            descripcion=f"Venta tarjeta {venta.producto.nombre} (x{venta.cantidad})",
                            tipo_cuenta_debito='activo',
                            tipo_cuenta_credito='ingreso'
                        )
                    else:  # crédito
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Cuentas por Cobrar',
                            cuenta_credito_nombre='Ventas',
                            monto=venta.monto,
                            descripcion=f"Venta crédito {venta.producto.nombre} (x{venta.cantidad}) - {venta.cliente_display}",
                            tipo_cuenta_debito='activo',
                            tipo_cuenta_credito='ingreso'
                        )
                    
                    # 2. Calcular costo REAL del producto
                    # Para productos manufacturados, usar precio_costo calculado
                    # Para productos comerciales, usar precio_unitario (costo de compra)
                    if empresa.categoria == 'manufactura':
                        # Buscar si es producto manufacturado
                        try:
                            from empresa.models import ProductoManufacturado
                            producto_manuf = ProductoManufacturado.objects.get(
                                empresa=empresa, codigo=venta.producto.codigo
                            )
                            costo_unitario = producto_manuf.precio_costo or producto_manuf.costo_produccion
                        except ProductoManufacturado.DoesNotExist:
                            costo_unitario = venta.producto.precio_unitario
                    else:
                        # Para comercio/servicios, usar precio_unitario como costo
                        costo_unitario = venta.producto.precio_unitario
                    
                    costo_total = venta.cantidad * costo_unitario
                    
                    if costo_total > 0:  # Solo registrar si hay costo
                        if empresa.categoria == 'servicios':
                            # SERVICIOS: Débito Costo Ventas + Crédito Caja (costo directo)
                            registrar_movimiento_contable(
                                empresa=empresa,
                                cuenta_debito_nombre='Costo de Ventas',
                                cuenta_credito_nombre='Caja/Banco',
                                monto=costo_total,
                                descripcion=f"Costo directo servicio {venta.producto.nombre} (x{venta.cantidad})"
                            )
                        else:
                            # COMERCIO: Débito Costo Ventas + Crédito Inventario
                            registrar_movimiento_contable(
                                empresa=empresa,
                                cuenta_debito_nombre='Costo de Ventas',
                                cuenta_credito_nombre='Inventario',
                                monto=costo_total,
                                descripcion=f"Costo de venta {venta.producto.nombre} (x{venta.cantidad})"
                            )
                if empresa.categoria == 'servicios':
                    messages.success(request, f'Servicio registrado: {venta.producto.nombre} - Venta: ${venta.monto}, Costo: ${costo_total}')
                else:
                    messages.success(request, 'Venta registrada correctamente.')
                return redirect('empresa:home')
            except Exception as e:
                messages.error(request, f'Error al registrar venta: {e}')
    else:
        form = VentaForm(empresa=empresa)

    # 📦 Preparamos la lista de productos con id, código, precio y stock
    productos = Producto.objects.filter(empresa=empresa)
    productos_json = [
        {
            'id': p.id,
            'codigo': p.codigo,
            'codigo_barras': p.codigo_barras or '',
            'nombre': p.nombre,
            'precio_costo': float(p.precio_unitario),  # Precio de costo
            'precio_venta': float(p.pvp) if p.pvp else float(p.precio_unitario),  # PVP o precio_unitario como fallback
            'stock': p.stock,
        }
        for p in productos
    ]
    context = {
        'form': form, 
        'productos_json': productos_json,
        'servicios': servicios,
        'es_servicios': empresa.categoria == 'servicios'
    }
    return render(request, 'empresa/crear_venta.html', context)

def procesar_venta_servicio(request, empresa):
    """Procesar venta específica de servicio"""
    try:
        from empresa.models import TipoServicio, Producto
        
        servicio_id = request.POST.get('servicio_id')
        cliente_nombre = request.POST.get('cliente_nombre', '').strip()
        cantidad = float(request.POST.get('cantidad', 1))
        precio_unitario = float(request.POST.get('precio_unitario', 0))
        tipo_pago = request.POST.get('tipo_pago', 'contado')
        
        # Calcular IVA
        incluye_iva = request.POST.get('incluirIva') == 'on'
        tasa_iva = float(request.POST.get('tasa_iva', 12)) if incluye_iva else 0
        monto_neto = cantidad * precio_unitario
        iva = monto_neto * (tasa_iva / 100) if incluye_iva else 0
        monto_total = monto_neto + iva
        
        servicio = TipoServicio.objects.get(id=servicio_id, empresa=empresa)
        
        # Crear o buscar producto equivalente
        producto, created = Producto.objects.get_or_create(
            empresa=empresa,
            codigo=f'SERV-{servicio.id}',
            defaults={
                'nombre': servicio.nombre,
                'descripcion': f'Servicio: {servicio.descripcion}',
                'precio_unitario': servicio.costo_directo,
                'pvp': servicio.precio_base,
                'stock': 999999
            }
        )
        
        # Crear venta
        venta = Venta.objects.create(
            empresa=empresa,
            cliente_nombre=cliente_nombre or 'Cliente General',
            producto=producto,
            cantidad=int(cantidad),
            precio_unitario=precio_unitario,
            monto_neto=monto_neto,
            iva=iva,
            monto=monto_total,
            tasa_iva=tasa_iva,
            tipo_pago=tipo_pago
        )
        
        messages.success(request, f'Venta de servicio "{servicio.nombre}" registrada por ${monto_total:.2f}')
        return redirect('empresa:home')
        
    except Exception as e:
        messages.error(request, f'Error al registrar venta de servicio: {str(e)}')
        return redirect('empresa:crear_venta')

def procesar_venta_servicio(request, empresa):
    """Procesar venta específica de servicio"""
    try:
        from empresa.models import TipoServicio, Producto
        
        servicio_id = request.POST.get('servicio_id')
        cliente_nombre = request.POST.get('cliente_nombre', '').strip()
        cantidad = float(request.POST.get('cantidad', 1))
        precio_unitario = float(request.POST.get('precio_unitario', 0))
        tipo_pago = request.POST.get('tipo_pago', 'contado')
        incluye_iva = request.POST.get('incluye_iva') == 'on'
        tasa_iva = float(request.POST.get('tasa_iva', 12)) if incluye_iva else 0
        
        servicio = TipoServicio.objects.get(id=servicio_id, empresa=empresa)
        
        # Calcular montos
        monto_neto = cantidad * precio_unitario
        iva = monto_neto * (tasa_iva / 100) if incluye_iva else 0
        monto_total = monto_neto + iva
        
        # Crear o buscar producto equivalente
        producto, created = Producto.objects.get_or_create(
            empresa=empresa,
            codigo=f'SERV-{servicio.id}',
            defaults={
                'nombre': servicio.nombre,
                'descripcion': f'Servicio: {servicio.descripcion}',
                'precio_unitario': servicio.costo_directo,
                'pvp': servicio.precio_base,
                'stock': 999999
            }
        )
        
        # Crear venta
        venta = Venta.objects.create(
            empresa=empresa,
            cliente_nombre=cliente_nombre or 'Cliente General',
            producto=producto,
            cantidad=int(cantidad),
            precio_unitario=precio_unitario,
            monto_neto=monto_neto,
            iva=iva,
            monto=monto_total,
            tasa_iva=tasa_iva,
            tipo_pago=tipo_pago
        )
        
        messages.success(request, f'Venta de servicio "{servicio.nombre}" registrada por ${monto_total:.2f}')
        return redirect('empresa:home')
        
    except Exception as e:
        messages.error(request, f'Error al registrar venta de servicio: {str(e)}')
        return redirect('empresa:crear_venta')

@login_required
@require_power('puede_registrar_ventas')
def listar_ventas(request):
    empresa = request.user.empresa
    ventas = Venta.objects.filter(empresa=empresa).order_by('-fecha')

    # Filtros avanzados
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

    # Estadísticas generales (opcional, para futuras mejoras)
    total_ventas = ventas.aggregate(total=Sum('monto'))['total'] or 0
    total_transacciones = ventas.count()
    promedio_venta = ventas.aggregate(promedio=Avg('monto'))['promedio'] or 0

    contexto = {
        'ventas': ventas,
        'total_ventas': total_ventas,
        'total_transacciones': total_transacciones,
        'promedio_venta': promedio_venta,
    }
    return render(request, 'empresa/listar_ventas.html', contexto)
