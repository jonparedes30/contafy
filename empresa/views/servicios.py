from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from empresa.models import TipoServicio, MaterialServicio, Empresa
from empresa.decorators import empresa_required

@login_required
@empresa_required
def listar_tipos_servicios(request):
    """Lista todos los tipos de servicios de la empresa"""
    servicios = TipoServicio.objects.filter(
        empresa=request.user.empresa,
        activo=True
    ).order_by('nombre')
    
    context = {
        'servicios': servicios,
        'total_servicios': servicios.count(),
    }
    return render(request, 'empresa/servicios/listar_servicios.html', context)

@login_required
@empresa_required
def crear_tipo_servicio(request):
    """Crear un nuevo tipo de servicio"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Validar campos requeridos
                nombre = request.POST.get('nombre', '').strip()
                if not nombre:
                    messages.error(request, 'El nombre del servicio es requerido.')
                    return render(request, 'empresa/servicios/crear_servicio.html')
                
                # Convertir valores numéricos de forma segura
                try:
                    precio_base = float(request.POST.get('precio_base', 0) or 0)
                except (ValueError, TypeError):
                    precio_base = 0
                
                try:
                    costo_directo = float(request.POST.get('costo_directo', 0) or 0)
                except (ValueError, TypeError):
                    costo_directo = 0
                
                try:
                    tiempo_estimado = int(request.POST.get('tiempo_estimado', 0) or 0) if request.POST.get('tiempo_estimado') else None
                except (ValueError, TypeError):
                    tiempo_estimado = None
                
                servicio = TipoServicio.objects.create(
                    empresa=request.user.empresa,
                    nombre=nombre,
                    descripcion=request.POST.get('descripcion', '').strip(),
                    precio_base=precio_base,
                    costo_directo=costo_directo,
                    tiempo_estimado=tiempo_estimado,
                    unidad_medida=request.POST.get('unidad_medida', 'Servicio'),
                )
                
                messages.success(request, f'Servicio "{servicio.nombre}" creado exitosamente.')
                return redirect('empresa:listar_tipos_servicios')
                
        except Exception as e:
            messages.error(request, f'Error al crear el servicio: {str(e)}')
    
    return render(request, 'empresa/servicios/crear_servicio.html')

@login_required
@empresa_required
def editar_tipo_servicio(request, servicio_id):
    """Editar un tipo de servicio existente"""
    servicio = get_object_or_404(TipoServicio, id=servicio_id, empresa=request.user.empresa)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Validar campos requeridos
                nombre = request.POST.get('nombre', '').strip()
                if not nombre:
                    messages.error(request, 'El nombre del servicio es requerido.')
                    context = {'servicio': servicio}
                    return render(request, 'empresa/servicios/editar_servicio.html', context)
                
                # Convertir valores numéricos de forma segura
                try:
                    precio_base = float(request.POST.get('precio_base', 0) or 0)
                except (ValueError, TypeError):
                    precio_base = 0
                
                try:
                    costo_directo = float(request.POST.get('costo_directo', 0) or 0)
                except (ValueError, TypeError):
                    costo_directo = 0
                
                try:
                    tiempo_estimado = int(request.POST.get('tiempo_estimado', 0) or 0) if request.POST.get('tiempo_estimado') else None
                except (ValueError, TypeError):
                    tiempo_estimado = None
                
                servicio.nombre = nombre
                servicio.descripcion = request.POST.get('descripcion', '').strip()
                servicio.precio_base = precio_base
                servicio.costo_directo = costo_directo
                servicio.tiempo_estimado = tiempo_estimado
                servicio.unidad_medida = request.POST.get('unidad_medida', 'Servicio')
                servicio.save()
                
                messages.success(request, f'Servicio "{servicio.nombre}" actualizado exitosamente.')
                return redirect('empresa:listar_tipos_servicios')
                
        except Exception as e:
            messages.error(request, f'Error al actualizar el servicio: {str(e)}')
    
    context = {
        'servicio': servicio,
    }
    return render(request, 'empresa/servicios/editar_servicio.html', context)

@login_required
@empresa_required
def eliminar_tipo_servicio(request, servicio_id):
    """Eliminar (desactivar) un tipo de servicio"""
    servicio = get_object_or_404(TipoServicio, id=servicio_id, empresa=request.user.empresa)
    
    if request.method == 'POST':
        servicio.activo = False
        servicio.save()
        messages.success(request, f'Servicio "{servicio.nombre}" eliminado exitosamente.')
        return redirect('empresa:listar_tipos_servicios')
    
    context = {
        'servicio': servicio,
    }
    return render(request, 'empresa/servicios/eliminar_servicio.html', context)