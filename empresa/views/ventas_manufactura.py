# empresa/views/ventas_manufactura.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from empresa.models import Venta, ProductoManufacturado
from empresa.decorators import require_power
from empresa.forms import VentaForm
from empresa.views.contabilidad import registrar_movimiento_contable
from django.db import transaction
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q
from django import forms

class VentaManufacturaForm(forms.Form):
    cliente_fk = forms.ModelChoiceField(
        queryset=None, 
        required=False, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cliente_nombre = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del cliente (si no está registrado)'
        })
    )
    producto = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'id': 'id_cantidad', 'class': 'form-control'})
    )
    precio_unitario = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'id': 'id_precio_unitario', 
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Precio de venta'
        })
    )
    tipo_pago = forms.ChoiceField(
        choices=[('contado', 'Contado'), ('credito', 'Crédito')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    monto = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
        })
    )
    
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        if empresa:
            from empresa.models import Cliente
            self.fields['cliente_fk'].queryset = Cliente.objects.filter(empresa=empresa, activo=True)
            self.fields['producto'].queryset = ProductoManufacturado.objects.filter(
                empresa=empresa, activo=True
            )

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        precio_unitario = cleaned_data.get('precio_unitario')
        
        if cantidad and precio_unitario:
            cleaned_data['monto'] = cantidad * precio_unitario
        
        return cleaned_data


@login_required
@require_power('puede_registrar_ventas')
def crear_venta_manufactura(request):
    """Vista específica para ventas de productos manufacturados"""
    empresa = request.user.empresa
    
    if empresa.categoria != 'manufactura':
        messages.error(request, 'Esta función es solo para empresas de manufactura.')
        return redirect('empresa:home')

    # Preparar productos del catálogo para JavaScript
    productos = ProductoManufacturado.objects.filter(empresa=empresa, activo=True)
    productos_json = [
        {
            'id': p.id,
            'codigo': p.codigo,
            'nombre': p.nombre,
            'precio_venta': float(p.precio_venta),
            'costo_produccion': float(p.costo_produccion),
        }
        for p in productos
    ]

    if request.method == 'POST':
        form = VentaManufacturaForm(request.POST, empresa=empresa)
        print(f"DEBUG - Form data: {request.POST}")
        print(f"DEBUG - Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"DEBUG - Form errors: {form.errors}")
        if form.is_valid():
            print(f"DEBUG - Iniciando proceso de venta")
            try:
                with transaction.atomic():
                    # Obtener el ProductoManufacturado antes de guardar
                    producto_manuf_id = form.cleaned_data['producto'].id
                    producto_manuf = ProductoManufacturado.objects.get(id=producto_manuf_id)
                    print(f"DEBUG - Producto manufacturado obtenido: {producto_manuf.nombre}")
                    
                    # Crear un Producto temporal basado en el ProductoManufacturado
                    from empresa.models import Producto
                    producto_temp, created = Producto.objects.get_or_create(
                        codigo=producto_manuf.codigo,
                        empresa=empresa,
                        defaults={
                            'nombre': producto_manuf.nombre,
                            'descripcion': producto_manuf.descripcion,
                            'precio_unitario': producto_manuf.precio_venta,
                            'stock': 0,
                            'categoria': producto_manuf.categoria,
                            'creado_por': request.user
                        }
                    )
                    
                    # Si ya existía, actualizar datos
                    if not created:
                        producto_temp.nombre = producto_manuf.nombre
                        producto_temp.descripcion = producto_manuf.descripcion
                        producto_temp.precio_unitario = producto_manuf.precio_venta
                        producto_temp.categoria = producto_manuf.categoria
                        producto_temp.save()
                    
                    # Crear la venta manualmente
                    venta = Venta.objects.create(
                        empresa=empresa,
                        cliente_fk=form.cleaned_data.get('cliente_fk'),
                        cliente_nombre=form.cleaned_data.get('cliente_nombre', ''),
                        producto=producto_temp,
                        cantidad=form.cleaned_data['cantidad'],
                        precio_unitario=form.cleaned_data['precio_unitario'],
                        monto=form.cleaned_data['monto'],
                        tipo_pago=form.cleaned_data['tipo_pago'],
                        creado_por=request.user
                    )
                    
                    print(f"DEBUG - Venta creada: ID={venta.id}, Producto={venta.producto.nombre}, Monto=${venta.monto}")
                    
                    # Verificar disponibilidad de materias primas
                    receta = producto_manuf.receta.all()
                    print(f"DEBUG - Receta obtenida: {receta.count()} ingredientes")
                    materias_faltantes = []
                    
                    for ingrediente in receta:
                        cantidad_necesaria = ingrediente.cantidad_necesaria * venta.cantidad
                        if ingrediente.materia_prima.stock_actual < cantidad_necesaria:
                            materias_faltantes.append({
                                'materia': ingrediente.materia_prima.nombre,
                                'necesaria': cantidad_necesaria,
                                'disponible': ingrediente.materia_prima.stock_actual
                            })
                    
                    if materias_faltantes:
                        error_msg = 'Materias primas insuficientes: '
                        for faltante in materias_faltantes:
                            error_msg += f"{faltante['materia']} (necesita {faltante['necesaria']}, disponible {faltante['disponible']}); "
                        messages.error(request, error_msg)
                        return render(request, 'empresa/manufactura/crear_venta.html', {
                            'form': form, 
                            'productos_json': productos_json
                        })
                    
                    # Fabricar automáticamente: consumir materias primas
                    from empresa.models import ConsumoMateriaPrima
                    costo_total_produccion = 0
                    
                    for ingrediente in receta:
                        cantidad_consumida = ingrediente.cantidad_necesaria * venta.cantidad
                        costo_total = cantidad_consumida * ingrediente.materia_prima.precio_unitario
                        costo_total_produccion += costo_total
                        
                        # Crear registro de consumo
                        ConsumoMateriaPrima.objects.create(
                            empresa=empresa,
                            orden_produccion=None,  # Fabricación automática
                            materia_prima=ingrediente.materia_prima,
                            cantidad_consumida=cantidad_consumida,
                            costo_unitario=ingrediente.materia_prima.precio_unitario,
                            costo_total=costo_total
                        )
                        
                        # Reducir stock de materia prima
                        ingrediente.materia_prima.stock_actual -= cantidad_consumida
                        ingrediente.materia_prima.save()
                    
                    # Verificar y crear saldo inicial en Caja si es necesario
                    from empresa.models import CuentaContable
                    cuenta_caja, created = CuentaContable.objects.get_or_create(
                        empresa=empresa,
                        nombre='Caja/Banco',
                        defaults={'tipo': 'activo'}
                    )
                    
                    # Si la cuenta tiene saldo negativo o cero, crear capital inicial
                    if cuenta_caja.valor <= 0:
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Caja/Banco',
                            cuenta_credito_nombre='Capital Social',
                            monto=10000,  # Saldo inicial suficiente
                            descripcion="Capital inicial para operaciones"
                        )
                    
                    # Registrar la venta
                    if venta.tipo_pago == 'contado':
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Caja/Banco',
                            cuenta_credito_nombre='Ventas',
                            monto=venta.monto,
                            descripcion=f"Venta de {venta.producto.nombre} (x{venta.cantidad})"
                        )
                    else:
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Cuentas por Cobrar',
                            cuenta_credito_nombre='Ventas',
                            monto=venta.monto,
                            descripcion=f"Venta a crédito de {venta.producto.nombre} (x{venta.cantidad})"
                        )
                    
                    # DESPUÉS el costo de ventas
                    print(f"DEBUG - Venta: ${venta.monto}, Costo producción: ${costo_total_produccion}, Margen: ${venta.monto - costo_total_produccion}")
                    registrar_movimiento_contable(
                        empresa=empresa,
                        cuenta_debito_nombre='Costo de Ventas',
                        cuenta_credito_nombre='Inventario de Materias Primas',
                        monto=costo_total_produccion,
                        descripcion=f"Costo de producción para {venta.cantidad} unidades de {producto_manuf.nombre}"
                    )
                    
                    messages.success(request, f'Venta registrada: {venta.cantidad} unidades de {producto_manuf.nombre} por ${venta.monto}')
                    print(f"DEBUG - Redirigiendo a resumen financiero")
                    return redirect('empresa:resumen_financiero')
            except Exception as e:
                print(f"DEBUG - Error en transacción: {e}")
                messages.error(request, f'Error al registrar venta: {e}')
    else:
        form = VentaManufacturaForm(empresa=empresa)
    
    return render(request, 'empresa/manufactura/crear_venta.html', {
        'form': form, 
        'productos_json': productos_json
    })


@login_required
@require_power('puede_registrar_ventas')
def listar_ventas_manufactura(request):
    """Vista específica para listar ventas de productos manufacturados"""
    empresa = request.user.empresa
    
    if empresa.categoria != 'manufactura':
        messages.error(request, 'Esta función es solo para empresas de manufactura.')
        return redirect('empresa:home')
    
    # Solo ventas de productos manufacturados
    productos_manuf_codigos = ProductoManufacturado.objects.filter(
        empresa=empresa
    ).values_list('codigo', flat=True)
    
    ventas = Venta.objects.filter(
        empresa=empresa,
        producto__codigo__in=productos_manuf_codigos
    ).order_by('-fecha')

    # Filtros
    buscar = request.GET.get('buscar', '').strip()
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if buscar:
        ventas = ventas.filter(
            Q(producto__nombre__icontains=buscar) |
            Q(cliente_nombre__icontains=buscar)
        )
    if fecha_desde:
        ventas = ventas.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        ventas = ventas.filter(fecha__date__lte=fecha_hasta)

    # Estadísticas
    total_ventas = ventas.aggregate(total=Sum('monto'))['total'] or 0
    total_transacciones = ventas.count()
    promedio_venta = ventas.aggregate(promedio=Avg('monto'))['promedio'] or 0

    contexto = {
        'ventas': ventas,
        'total_ventas': total_ventas,
        'total_transacciones': total_transacciones,
        'promedio_venta': promedio_venta,
    }
    return render(request, 'empresa/manufactura/listar_ventas.html', contexto)