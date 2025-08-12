from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from empresa.models import ModuloAprendizaje, Leccion, ProgresoUsuario, PerfilAprendizaje

@login_required
def dashboard_aprendizaje(request):
    """Dashboard principal del sistema de aprendizaje"""
    usuario = request.user
    
    # Crear perfil de aprendizaje si no existe
    perfil, created = PerfilAprendizaje.objects.get_or_create(usuario=usuario)
    
    # Obtener módulos según el tipo de empresa del usuario
    tipo_empresa = usuario.empresa.categoria if usuario.empresa else 'comercial'
    modulos = ModuloAprendizaje.objects.filter(
        tipo_empresa=tipo_empresa,
        activo=True
    ).order_by('orden')
    
    # Calcular progreso por módulo
    progreso_modulos = {}
    for modulo in modulos:
        lecciones_total = modulo.lecciones.filter(activa=True).count()
        lecciones_completadas = ProgresoUsuario.objects.filter(
            usuario=usuario,
            leccion__modulo=modulo,
            completada=True
        ).count()
        
        porcentaje = (lecciones_completadas / lecciones_total * 100) if lecciones_total > 0 else 0
        
        progreso_modulos[modulo.id] = {
            'porcentaje': round(porcentaje, 1),
            'completadas': lecciones_completadas,
            'total': lecciones_total,
            'desbloqueado': True  # Por ahora todos desbloqueados
        }
    
    context = {
        'perfil': perfil,
        'modulos': modulos,
        'progreso_modulos': progreso_modulos,
        'tipo_empresa': tipo_empresa,
    }
    
    return render(request, 'empresa/aprendizaje/dashboard.html', context)

@login_required
def modulo_detalle(request, modulo_id):
    """Detalle de un módulo específico"""
    modulo = get_object_or_404(ModuloAprendizaje, id=modulo_id, activo=True)
    
    # Verificar que el módulo corresponde al tipo de empresa del usuario
    if usuario.empresa and modulo.tipo_empresa != usuario.empresa.categoria:
        messages.error(request, 'No tienes acceso a este módulo.')
        return redirect('empresa:aprendizaje_dashboard')
    
    # Obtener lecciones del módulo
    lecciones = modulo.lecciones.filter(activa=True).order_by('orden')
    
    # Obtener progreso del usuario en cada lección
    progreso_lecciones = {}
    for leccion in lecciones:
        try:
            progreso = ProgresoUsuario.objects.get(usuario=request.user, leccion=leccion)
            progreso_lecciones[leccion.id] = {
                'completada': progreso.completada,
                'puntuacion': progreso.puntuacion,
                'intentos': progreso.intentos
            }
        except ProgresoUsuario.DoesNotExist:
            progreso_lecciones[leccion.id] = {
                'completada': False,
                'puntuacion': 0,
                'intentos': 0
            }
    
    context = {
        'modulo': modulo,
        'lecciones': lecciones,
        'progreso_lecciones': progreso_lecciones,
    }
    
    return render(request, 'empresa/aprendizaje/modulo_detalle.html', context)

@login_required
def leccion_detalle(request, leccion_id):
    """Detalle de una lección específica"""
    leccion = get_object_or_404(Leccion, id=leccion_id, activa=True)
    
    # Obtener o crear progreso del usuario
    progreso, created = ProgresoUsuario.objects.get_or_create(
        usuario=request.user,
        leccion=leccion
    )
    
    if request.method == 'POST':
        # Marcar lección como completada
        if not progreso.completada:
            progreso.completada = True
            progreso.tiempo_completado = timezone.now()
            progreso.save()
            
            # Otorgar XP al usuario
            perfil, _ = PerfilAprendizaje.objects.get_or_create(usuario=request.user)
            perfil.xp_total += leccion.puntos_xp
            
            # Calcular nuevo nivel
            nuevo_nivel = (perfil.xp_total // 100) + 1
            if nuevo_nivel > perfil.nivel:
                perfil.nivel = nuevo_nivel
                messages.success(request, f'¡Felicidades! Has subido al nivel {nuevo_nivel}!')
            
            perfil.save()
            
            messages.success(request, f'¡Lección completada! +{leccion.puntos_xp} XP')
            return redirect('empresa:aprendizaje_modulo', modulo_id=leccion.modulo.id)
    
    context = {
        'leccion': leccion,
        'progreso': progreso,
    }
    
    return render(request, 'empresa/aprendizaje/leccion_detalle.html', context)