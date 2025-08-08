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
                servicio = TipoServicio.objects.create(
                    empresa=request.user.empresa,
                    nombre=request.POST.get('nombre'),
                    descripcion=request.POST.get('descripcion', ''),
                    precio_base=float(request.POST.get('precio_base', 0)),
                    costo_directo=float(request.POST.get('costo_directo', 0)),
                    tiempo_estimado=int(request.POST.get('tiempo_estimado', 0)) if request.POST.get('tiempo_estimado') else None,
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
                servicio.nombre = request.POST.get('nombre')
                servicio.descripcion = request.POST.get('descripcion', '')
                servicio.precio_base = float(request.POST.get('precio_base', 0))
                servicio.costo_directo = float(request.POST.get('costo_directo', 0))
                servicio.tiempo_estimado = int(request.POST.get('tiempo_estimado', 0)) if request.POST.get('tiempo_estimado') else None
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