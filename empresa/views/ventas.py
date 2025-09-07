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
from django.http import JsonResponse
import json

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
                    
                    # Crear asientos contables usando el servicio centralizado
                    venta.crear_asientos_contables()
                    
                    # 1. Registrar la venta según tipo de pago (LEGACY - mantener por compatibilidad)
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
            'nombre': f"{p.nombre} ({p.descripcion})" if p.descripcion else p.nombre,
            'descripcion': p.descripcion or '',
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

    # Verificar si el usuario es propietario (no empleado)
    # Si el usuario no tiene atributo 'poderes', es propietario
    # Si es superuser, también puede editar
    es_propietario = True  # Por defecto, permitir edición
    if hasattr(request.user, 'poderes'):
        # Si tiene poderes, es empleado, no propietario
        es_propietario = False
    if request.user.is_superuser:
        # Superuser siempre puede editar
        es_propietario = True

    contexto = {
        'ventas': ventas,
        'total_ventas': total_ventas,
        'total_transacciones': total_transacciones,
        'promedio_venta': promedio_venta,
        'es_propietario': es_propietario,
    }
    return render(request, 'empresa/listar_ventas.html', contexto)

@login_required
def editar_venta(request, venta_id):
    """Editar venta - solo para propietarios"""
    from django.shortcuts import get_object_or_404
    
    # Verificar que sea propietario (no empleado)
    if hasattr(request.user, 'poderes') and not request.user.is_superuser:
        messages.error(request, 'Solo el propietario puede editar ventas.')
        return redirect('empresa:listar_ventas')
    
    empresa = request.user.empresa
    venta = get_object_or_404(Venta, id=venta_id, empresa=empresa)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Restaurar stock anterior
                venta.producto.stock += venta.cantidad
                
                # Actualizar datos
                venta.cliente_nombre = request.POST.get('cliente_nombre', venta.cliente_nombre)
                venta.cantidad = int(request.POST.get('cantidad', venta.cantidad))
                venta.precio_unitario = float(request.POST.get('precio_unitario', venta.precio_unitario))
                
                # Recalcular montos
                venta.monto_neto = venta.cantidad * venta.precio_unitario
                venta.iva = venta.monto_neto * (venta.tasa_iva / 100)
                venta.monto = venta.monto_neto + venta.iva
                
                # Actualizar stock nuevo
                venta.producto.stock -= venta.cantidad
                venta.producto.save()
                venta.save()
                
                messages.success(request, 'Venta actualizada correctamente.')
                return redirect('empresa:home')
        except Exception as e:
            messages.error(request, f'Error al actualizar venta: {str(e)}')
    
    productos = Producto.objects.filter(empresa=empresa)
    context = {
        'venta': venta,
        'productos': productos
    }
    return render(request, 'empresa/editar_venta.html', context)

@login_required
def eliminar_venta(request, venta_id):
    """Eliminar venta - solo para propietarios"""
    from django.shortcuts import get_object_or_404
    
    # Verificar que sea propietario (no empleado)
    if hasattr(request.user, 'poderes') and not request.user.is_superuser:
        messages.error(request, 'Solo el propietario puede eliminar ventas.')
        return redirect('empresa:listar_ventas')
    
    empresa = request.user.empresa
    venta = get_object_or_404(Venta, id=venta_id, empresa=empresa)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Guardar datos antes de eliminar
                producto_nombre = venta.producto.nombre
                cantidad_restaurar = venta.cantidad
                producto = venta.producto
                
                # Eliminar cuenta por cobrar si existe
                from empresa.models import CuentaPorCobrar
                CuentaPorCobrar.objects.filter(venta=venta).delete()
                
                # Eliminar venta primero
                venta.delete()
                
                # Restaurar stock después de eliminar
                producto.stock += cantidad_restaurar
                producto.save()
                
                messages.success(request, f'Venta de {producto_nombre} eliminada correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar venta: {str(e)}')
            import logging
            logging.error(f'Error eliminando venta {venta_id}: {str(e)}')
    
    return redirect('empresa:home')

@login_required
@require_power('puede_registrar_ventas')
def crear_venta_multiple(request):
    """Vista para crear ventas múltiples"""
    empresa = request.user.empresa
    
    if request.method == 'GET':
        productos = Producto.objects.filter(empresa=empresa, stock__gt=0)
        servicios = []
        if empresa.categoria == 'servicios':
            from empresa.models import TipoServicio
            servicios_queryset = TipoServicio.objects.filter(empresa=empresa, activo=True)
            servicios = [{
                'id': s.id,
                'nombre': s.nombre,
                'precio_base': float(s.precio_base),
                'stock': 999999
            } for s in servicios_queryset]
        
        context = {
            'productos': productos,
            'servicios': servicios,
            'es_servicios': empresa.categoria == 'servicios'
        }
        return render(request, 'empresa/crear_venta_multiple.html', context)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            productos_venta = data.get('productos', [])
            cliente_nombre = data.get('cliente_nombre', '').strip()
            incluir_iva = data.get('incluir_iva', False)
            tipo_pago = data.get('tipo_pago', 'contado')
            monto_recibido = float(data.get('monto_recibido', 0))
            
            if not productos_venta:
                return JsonResponse({'success': False, 'error': 'No hay productos en la venta'})
            
            with transaction.atomic():
                total_venta = 0
                ventas_creadas = []
                
                for item in productos_venta:
                    producto_id = item['id']
                    cantidad = int(item['cantidad'])
                    precio = float(item['precio'])
                    
                    if empresa.categoria == 'servicios':
                        from empresa.models import TipoServicio
                        servicio = TipoServicio.objects.get(id=producto_id, empresa=empresa)
                        producto, created = Producto.objects.get_or_create(
                            empresa=empresa,
                            codigo=f'SERV-{servicio.id}',
                            defaults={
                                'nombre': servicio.nombre,
                                'precio_unitario': servicio.costo_directo,
                                'pvp': servicio.precio_base,
                                'stock': 999999
                            }
                        )
                    else:
                        producto = Producto.objects.get(id=producto_id, empresa=empresa)
                        if producto.stock < cantidad:
                            return JsonResponse({
                                'success': False, 
                                'error': f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}'
                            })
                    
                    monto_neto = cantidad * precio
                    iva = monto_neto * 0.15 if incluir_iva else 0
                    monto_total = monto_neto + iva
                    
                    venta = Venta.objects.create(
                        empresa=empresa,
                        cliente_nombre=cliente_nombre or 'Cliente General',
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        monto_neto=monto_neto,
                        iva=iva,
                        monto=monto_total,
                        tasa_iva=15 if incluir_iva else 0,
                        tipo_pago=tipo_pago,
                        creado_por=request.user
                    )
                    
                    if empresa.categoria != 'servicios':
                        producto.stock -= cantidad
                        producto.save()
                    
                    ventas_creadas.append(venta)
                    total_venta += monto_total
                
                if tipo_pago == 'contado' and monto_recibido < total_venta:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Monto insuficiente. Total: ${total_venta:.2f}, Recibido: ${monto_recibido:.2f}'
                    })
                
                cambio = monto_recibido - total_venta if tipo_pago == 'contado' else 0
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Venta procesada exitosamente. Total: ${total_venta:.2f}',
                    'total': total_venta,
                    'cambio': cambio,
                    'ventas_count': len(ventas_creadas)
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})
