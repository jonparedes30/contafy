from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from empresa.models import TipoServicio, Venta, Producto
from empresa.decorators import empresa_required

@login_required
@empresa_required
def crear_venta_servicio(request):
    """Crear venta específica para servicios"""
    
    # Obtener servicios de la empresa
    servicios = TipoServicio.objects.filter(
        empresa=request.user.empresa,
        activo=True
    ).order_by('nombre')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Obtener datos del formulario
                servicio_id = request.POST.get('servicio')
                cliente_nombre = request.POST.get('cliente_nombre', '').strip()
                cantidad = float(request.POST.get('cantidad', 1))
                precio_unitario = float(request.POST.get('precio_unitario', 0))
                tipo_pago = request.POST.get('tipo_pago', 'contado')
                incluye_iva = request.POST.get('incluye_iva') == 'on'
                tasa_iva = float(request.POST.get('tasa_iva', 12)) if incluye_iva else 0
                
                # Validaciones
                if not servicio_id:
                    messages.error(request, 'Debe seleccionar un servicio.')
                    return render(request, 'empresa/servicios/crear_venta.html', {'servicios': servicios})
                
                servicio = TipoServicio.objects.get(id=servicio_id, empresa=request.user.empresa)
                
                # Calcular montos
                monto_neto = cantidad * precio_unitario
                iva = monto_neto * (tasa_iva / 100) if incluye_iva else 0
                monto_total = monto_neto + iva
                
                # Crear o buscar producto equivalente para el servicio
                producto, created = Producto.objects.get_or_create(
                    empresa=request.user.empresa,
                    codigo=f'SERV-{servicio.id}',
                    defaults={
                        'nombre': servicio.nombre,
                        'descripcion': f'Servicio: {servicio.descripcion}',
                        'precio_unitario': servicio.precio_base,
                        'pvp': servicio.precio_base,
                        'stock': 999999  # Stock ilimitado para servicios
                    }
                )
                
                # Crear la venta
                venta = Venta.objects.create(
                    empresa=request.user.empresa,
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
                
                messages.success(request, f'Venta de servicio "{servicio.nombre}" registrada exitosamente por ${monto_total:.2f}')
                return redirect('empresa:listar_tipos_servicios')
                
        except TipoServicio.DoesNotExist:
            messages.error(request, 'Servicio no encontrado.')
        except Exception as e:
            messages.error(request, f'Error al registrar la venta: {str(e)}')
    
    context = {
        'servicios': servicios,
    }
    return render(request, 'empresa/servicios/crear_venta.html', context)