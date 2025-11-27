# empresa/views/manufactura.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.http import JsonResponse
from django.forms import formset_factory
from empresa.decorators import require_power
from empresa.models import (
    MateriaPrima, 
    ProductoManufacturado, 
    RecetaProduccion,
    OrdenProduccion
)
from empresa.forms import MateriaPrimaForm, ProductoManufacturadoForm


@login_required
@require_power('puede_gestionar_inventario')
def dashboard_manufactura(request):
    """Dashboard para manufactura"""
    if not request.user.empresa or request.user.empresa.categoria != 'manufactura':
        messages.warning(request, 'Esta sección es solo para empresas de manufactura.')
        return redirect('empresa:dashboard')
    
    empresa = request.user.empresa

    try:
        from empresa.presenters.manufactura_presenter import ManufacturaPresenter
        presenter = ManufacturaPresenter(empresa)
        context = presenter.to_context()
    except Exception as e:
        # Fallback: calcular in-place si el presenter falla
        print(f"Manufactura presenter error: {e}")
        total_materias_primas = MateriaPrima.objects.filter(empresa=empresa).count()
        total_productos = ProductoManufacturado.objects.filter(empresa=empresa, activo=True).count()
        ordenes_pendientes = OrdenProduccion.objects.filter(empresa=empresa, estado='pendiente').count()
        ordenes_en_proceso = OrdenProduccion.objects.filter(empresa=empresa, estado='en_proceso').count()
        materias_stock_bajo = MateriaPrima.objects.filter(empresa=empresa, stock_actual__lte=F('stock_minimo'))[:5]
        productos_stock_bajo = ProductoManufacturado.objects.filter(empresa=empresa, stock_actual__lte=F('stock_minimo'), activo=True)[:5]
        ordenes_recientes = OrdenProduccion.objects.filter(empresa=empresa).order_by('-creado_en')[:5]
        context = {
            'total_materias_primas': total_materias_primas,
            'total_productos': total_productos,
            'ordenes_pendientes': ordenes_pendientes,
            'ordenes_en_proceso': ordenes_en_proceso,
            'materias_stock_bajo': materias_stock_bajo,
            'productos_stock_bajo': productos_stock_bajo,
            'ordenes_recientes': ordenes_recientes,
        }

    return render(request, 'empresa/manufactura/dashboard.html', context)


@login_required
@require_power('puede_gestionar_inventario')
def listar_materias_primas(request):
    """Lista todas las materias primas"""
    if not request.user.empresa or request.user.empresa.categoria != 'manufactura':
        messages.warning(request, 'Esta sección es solo para empresas de manufactura.')
        return redirect('empresa:dashboard')
    
    empresa = request.user.empresa
    materias_primas = MateriaPrima.objects.filter(empresa=empresa).order_by('nombre')
    
    # Detectar si es móvil
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad'])
    
    template = 'empresa/manufactura/listar_materias_primas_mobile.html' if is_mobile else 'empresa/manufactura/listar_materias_primas.html'
    
    return render(request, template, {
        'materias_primas': materias_primas
    })


@login_required
@require_power('puede_gestionar_inventario')
def crear_materia_prima(request):
    """Crear nueva materia prima"""
    if not request.user.empresa or request.user.empresa.categoria != 'manufactura':
        messages.warning(request, 'Esta sección es solo para empresas de manufactura.')
        return redirect('empresa:dashboard')
    
    if request.method == 'POST':
        form = MateriaPrimaForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            try:
                materia_prima = form.save(commit=False)
                # CRÍTICO: Asignar empresa ANTES de cualquier otra operación
                if not materia_prima.empresa_id:
                    materia_prima.empresa = request.user.empresa
                if not materia_prima.creado_por_id:
                    materia_prima.creado_por = request.user
                materia_prima.save()
                
                # Registrar compra de materia prima como movimiento contable (opcional)
                try:
                    if materia_prima.stock_actual > 0:
                        from empresa.views.contabilidad import registrar_movimiento_contable
                        costo_total = materia_prima.stock_actual * materia_prima.precio_unitario
                        
                        registrar_movimiento_contable(
                            empresa=request.user.empresa,
                            cuenta_debito_nombre='Inventario de Materias Primas',
                            cuenta_credito_nombre='Caja/Banco',
                            monto=costo_total,
                            descripcion=f"Compra inicial de {materia_prima.nombre} - {materia_prima.stock_actual} {materia_prima.unidad_medida}",
                            tipo_cuenta_debito='activo',
                            tipo_cuenta_credito='activo'
                        )
                except Exception as e:
                    # No fallar si el movimiento contable falla
                    print(f"Error registrando movimiento contable: {e}")
                
                messages.success(request, 'Materia prima creada exitosamente.')
                return redirect('empresa:listar_materias_primas')
            except Exception as e:
                messages.error(request, f'Error al guardar materia prima: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = MateriaPrimaForm(empresa=request.user.empresa)
    
    return render(request, 'empresa/manufactura/crear_materia_prima.html', {
        'form': form
    })


@login_required
@require_power('puede_gestionar_inventario')
def listar_productos_manufacturados(request):
    """Lista todos los productos manufacturados"""
    empresa = request.user.empresa
    productos = ProductoManufacturado.objects.filter(empresa=empresa).order_by('nombre')
    
    return render(request, 'empresa/manufactura/listar_productos.html', {
        'productos': productos
    })


@login_required
@require_power('puede_editar_productos')
def crear_producto_manufacturado(request):
    """Crear nuevo producto manufacturado con su receta"""
    from django.db import transaction
    
    RecetaFormSet = formset_factory(RecetaProduccionForm, extra=3, can_delete=True, max_num=10)
    
    if request.method == 'POST':
        form = ProductoManufacturadoForm(request.POST, empresa=request.user.empresa)
        formset = RecetaFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Guardar producto
                    producto = form.save(commit=False)
                    producto.empresa = request.user.empresa
                    producto.creado_por = request.user
                    producto.save()
                    
                    # Guardar receta
                    recetas_guardadas = 0
                    for receta_form in formset:
                        if receta_form.cleaned_data and not receta_form.cleaned_data.get('DELETE', False):
                            materia_prima = receta_form.cleaned_data.get('materia_prima')
                            cantidad = receta_form.cleaned_data.get('cantidad_necesaria')
                            
                            if materia_prima and cantidad:
                                receta = receta_form.save(commit=False)
                                receta.producto = producto
                                receta.save()
                                recetas_guardadas += 1
                    
                    messages.success(request, f'Producto "{producto.nombre}" y receta creados exitosamente.')
                    return redirect('empresa:listar_productos_manufacturados')
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
        else:
            if not form.is_valid():
                messages.error(request, 'Por favor corrige los errores en el formulario del producto.')
            if not formset.is_valid():
                messages.error(request, 'Por favor corrige los errores en la receta.')
    else:
        form = ProductoManufacturadoForm(empresa=request.user.empresa)
        formset = RecetaFormSet()
        
        # Configurar empresa para cada formulario del formset
        for receta_form in formset:
            if hasattr(receta_form, 'fields'):
                receta_form.fields['materia_prima'].queryset = MateriaPrima.objects.filter(empresa=request.user.empresa)
    
    return render(request, 'empresa/manufactura/crear_producto.html', {
        'form': form,
        'formset': formset
    })


@login_required
def listar_ordenes_produccion(request):
    """Lista todas las órdenes de producción"""
    empresa = request.user.empresa
    ordenes = OrdenProduccion.objects.filter(empresa=empresa).order_by('-creado_en')
    
    return render(request, 'empresa/manufactura/listar_ordenes.html', {
        'ordenes': ordenes
    })


@login_required
def crear_orden_produccion(request):
    """Crear nueva orden de producción"""
    if request.method == 'POST':
        form = OrdenProduccionForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            orden = form.save()
            messages.success(request, f'Orden de producción {orden.numero_orden} creada exitosamente.')
            return redirect('empresa:listar_ordenes_produccion')
    else:
        form = OrdenProduccionForm(empresa=request.user.empresa)
    
    return render(request, 'empresa/manufactura/crear_orden.html', {
        'form': form
    })


@login_required
def detalle_orden_produccion(request, orden_id):
    """Ver detalle de una orden de producción"""
    empresa = request.user.empresa
    try:
        orden = OrdenProduccion.objects.get(id=orden_id, empresa=empresa)
    except OrdenProduccion.DoesNotExist:
        messages.error(request, 'Orden no encontrada o no pertenece a tu empresa.')
        return redirect('empresa:listar_ordenes_produccion')
    
    # Obtener consumos de materias primas
    consumos = ConsumoMateriaPrima.objects.filter(orden_produccion=orden)
    
    # Calcular costos
    costo_total = consumos.aggregate(total=Sum('costo_total'))['total'] or 0
    
    context = {
        'orden': orden,
        'consumos': consumos,
        'costo_total': costo_total,
    }
    
    return render(request, 'empresa/manufactura/detalle_orden.html', context)


@login_required
def iniciar_produccion(request, orden_id):
    """Iniciar producción de una orden"""
    if request.method == 'POST':
        empresa = request.user.empresa
        try:
            orden = OrdenProduccion.objects.get(id=orden_id, empresa=empresa)
        except OrdenProduccion.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Orden no encontrada o no pertenece a tu empresa'})
        
        if orden.estado == 'pendiente':
            # Verificar disponibilidad de materias primas
            receta = orden.producto.receta.all()
            materias_faltantes = []
            
            for ingrediente in receta:
                cantidad_necesaria = ingrediente.cantidad_necesaria * orden.cantidad_solicitada
                if ingrediente.materia_prima.stock_actual < cantidad_necesaria:
                    materias_faltantes.append({
                        'materia': ingrediente.materia_prima.nombre,
                        'necesaria': cantidad_necesaria,
                        'disponible': ingrediente.materia_prima.stock_actual
                    })
            
            if materias_faltantes:
                messages.error(request, 'No hay suficientes materias primas para iniciar la producción.')
                return JsonResponse({
                    'success': False,
                    'materias_faltantes': materias_faltantes
                })
            
            # Iniciar producción
            from django.utils import timezone
            orden.estado = 'en_proceso'
            orden.fecha_inicio = timezone.now()
            orden.save()
            
            # Consumir materias primas
            for ingrediente in receta:
                cantidad_consumida = ingrediente.cantidad_necesaria * orden.cantidad_solicitada
                
                # Crear registro de consumo
                ConsumoMateriaPrima.objects.create(
                    empresa=empresa,
                    orden_produccion=orden,
                    materia_prima=ingrediente.materia_prima,
                    cantidad_consumida=cantidad_consumida,
                    costo_unitario=ingrediente.materia_prima.precio_unitario,
                    costo_total=cantidad_consumida * ingrediente.materia_prima.precio_unitario
                )
                
                # Reducir stock
                ingrediente.materia_prima.stock_actual -= cantidad_consumida
                ingrediente.materia_prima.save()
            
            messages.success(request, f'Producción iniciada para orden {orden.numero_orden}.')
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'La orden no está en estado pendiente'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def completar_produccion(request, orden_id):
    """Completar producción de una orden"""
    if request.method == 'POST':
        empresa = request.user.empresa
        try:
            orden = OrdenProduccion.objects.get(id=orden_id, empresa=empresa)
        except OrdenProduccion.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Orden no encontrada o no pertenece a tu empresa'})
        
        if orden.estado == 'en_proceso':
            from django.utils import timezone
            
            # Completar orden
            orden.estado = 'completada'
            orden.fecha_fin = timezone.now()
            orden.cantidad_producida = orden.cantidad_solicitada
            orden.save()
            
            # Aumentar stock del producto
            orden.producto.stock_actual += orden.cantidad_solicitada
            orden.producto.save()
            
            # Registrar movimiento contable: Producto terminado
            try:
                from empresa.views.contabilidad import registrar_movimiento_contable
                
                # Calcular costo total de producción
                consumos = ConsumoMateriaPrima.objects.filter(orden_produccion=orden)
                costo_total_produccion = consumos.aggregate(total=Sum('costo_total'))['total'] or 0
                
                # Débito: Inventario de Productos Terminados
                # Crédito: Inventario de Materias Primas (ya se registró en el consumo)
                registrar_movimiento_contable(
                    empresa=empresa,
                    cuenta_debito_nombre='Inventario de Productos Terminados',
                    cuenta_credito_nombre='Inventario de Materias Primas',
                    monto=costo_total_produccion,
                    descripcion=f'Producción completada - {orden.cantidad_solicitada} unidades de {orden.producto.nombre}',
                    tipo_cuenta_debito='activo',
                    tipo_cuenta_credito='activo'
                )
            except Exception as e:
                print(f'Error registrando movimiento contable de producción: {e}')
            
            messages.success(request, f'Producción completada para orden {orden.numero_orden}.')
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'La orden no está en proceso'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@require_power('puede_editar_productos')
def editar_producto_manufacturado(request, producto_id):
    """Editar producto manufacturado y su receta"""
    empresa = request.user.empresa
    try:
        producto = ProductoManufacturado.objects.get(id=producto_id, empresa=empresa)
    except ProductoManufacturado.DoesNotExist:
        messages.error(request, 'Producto no encontrado o no pertenece a tu empresa.')
        return redirect('empresa:listar_productos_manufacturados')
    
    RecetaFormSet = formset_factory(RecetaProduccionForm, extra=1, can_delete=True, max_num=10)
    
    if request.method == 'POST':
        form = ProductoManufacturadoForm(request.POST, empresa=empresa, instance=producto)
        formset = RecetaFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                # Actualizar producto
                producto = form.save()
                
                # Eliminar receta anterior
                producto.receta.all().delete()
                
                # Guardar nueva receta
                for receta_form in formset:
                    if receta_form.cleaned_data and not receta_form.cleaned_data.get('DELETE', False):
                        receta = receta_form.save(commit=False)
                        receta.producto = producto
                        receta.save()
                
                messages.success(request, 'Producto actualizado exitosamente.')
                return redirect('empresa:listar_productos_manufacturados')
            except Exception as e:
                messages.error(request, f'Error al actualizar: {e}')
    else:
        form = ProductoManufacturadoForm(empresa=empresa, instance=producto)
        
        # Cargar receta existente
        receta_inicial = []
        for ingrediente in producto.receta.all():
            receta_inicial.append({
                'materia_prima': ingrediente.materia_prima,
                'cantidad_necesaria': ingrediente.cantidad_necesaria
            })
        
        formset = RecetaFormSet(initial=receta_inicial)
        
        # Configurar empresa para cada formulario del formset
        for receta_form in formset:
            if hasattr(receta_form, 'fields'):
                receta_form.fields['materia_prima'].queryset = MateriaPrima.objects.filter(empresa=empresa)
    
    return render(request, 'empresa/manufactura/editar_producto.html', {
        'form': form,
        'formset': formset,
        'producto': producto
    })


@login_required
def ver_receta_producto(request, producto_id):
    """Ver receta detallada de un producto manufacturado"""
    empresa = request.user.empresa
    producto = get_object_or_404(ProductoManufacturado, id=producto_id, empresa=empresa)
    
    receta = producto.receta.all()
    costo_total = sum(r.cantidad_necesaria * r.materia_prima.precio_unitario for r in receta)
    
    return render(request, 'empresa/manufactura/ver_receta.html', {
        'producto': producto,
        'receta': receta,
        'costo_total': costo_total
    })


@login_required
def cambiar_estado_producto(request, producto_id):
    """Cambiar estado activo/inactivo de un producto manufacturado"""
    if request.method == 'POST':
        empresa = request.user.empresa
        try:
            producto = ProductoManufacturado.objects.get(id=producto_id, empresa=empresa)
            
            # Cambiar estado
            producto.activo = not producto.activo
            producto.save()
            
            estado_texto = 'activado' if producto.activo else 'desactivado'
            messages.success(request, f'Producto {producto.nombre} {estado_texto} exitosamente.')
        except ProductoManufacturado.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Producto no encontrado o no pertenece a tu empresa'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
        return JsonResponse({
            'success': True, 
            'activo': producto.activo,
            'mensaje': f'Producto {estado_texto}'
        })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@require_power('puede_gestionar_inventario')
def crear_proveedor_ajax(request):
    """Crear proveedor desde AJAX para materias primas"""
    if request.method == 'POST':
        form = ProveedorForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            proveedor = form.save()
            return JsonResponse({
                'success': True,
                'proveedor': {
                    'id': proveedor.id,
                    'nombre': proveedor.nombre
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@require_power('puede_gestionar_inventario')
def editar_materia_prima(request, materia_id):
    """Editar materia prima"""
    empresa = request.user.empresa
    try:
        materia = MateriaPrima.objects.get(id=materia_id, empresa=empresa)
    except MateriaPrima.DoesNotExist:
        messages.error(request, 'Materia prima no encontrada.')
        return redirect('empresa:listar_materias_primas')
    
    if request.method == 'POST':
        form = MateriaPrimaForm(request.POST, empresa=empresa, instance=materia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia prima actualizada exitosamente.')
            return redirect('empresa:listar_materias_primas')
    else:
        form = MateriaPrimaForm(empresa=empresa, instance=materia)
    
    return render(request, 'empresa/manufactura/editar_materia_prima.html', {
        'form': form,
        'materia': materia
    })


@login_required
@require_power('puede_gestionar_inventario')
def listar_proveedores(request):
    """Lista todos los proveedores"""
    empresa = request.user.empresa
    proveedores = Proveedor.objects.filter(empresa=empresa, activo=True).order_by('nombre')
    
    return render(request, 'empresa/manufactura/listar_proveedores.html', {
        'proveedores': proveedores
    })