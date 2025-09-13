from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, ProgresoUsuario, PerfilAprendizaje
from empresa.services.gamificacion_service import GamificacionService
from empresa.services.recommendation_service import RecommendationService

@login_required
def aprendizaje_dashboard(request):
    """Dashboard principal de la Academia"""
    
    # Determinar tipo de empresa del usuario
    tipo_empresa = 'comercial'  # Default
    if hasattr(request.user, 'empresa_set') and request.user.empresa_set.exists():
        tipo_empresa = request.user.empresa_set.first().categoria
    
    # Obtener módulos disponibles
    modulos = ModuloAprendizaje.objects.filter(
        tipo_empresa=tipo_empresa,
        visible=True,
        activo=True
    ).prefetch_related('lecciones').order_by('orden')
    
    # Obtener progreso del usuario
    progreso_usuario = ProgresoUsuario.objects.filter(
        usuario=request.user
    ).select_related('leccion')
    
    # Crear diccionario de progreso por lección
    progreso_dict = {p.leccion_id: p for p in progreso_usuario}
    
    # Obtener perfil de aprendizaje
    perfil, created = PerfilAprendizaje.objects.get_or_create(usuario=request.user)
    
    # Obtener recomendaciones
    recomendaciones = RecommendationService.obtener_recomendaciones_personalizadas(
        request.user, limite=3
    )
    
    context = {
        'modulos': modulos,
        'progreso_dict': progreso_dict,
        'perfil': perfil,
        'recomendaciones': recomendaciones,
        'tipo_empresa': tipo_empresa,
    }
    
    return render(request, 'empresa/aprendizaje/dashboard.html', context)

@login_required
def leccion_interactiva(request, leccion_id):
    """Vista de lección interactiva estilo Duolingo"""
    
    leccion = get_object_or_404(
        Leccion, 
        id=leccion_id, 
        visible=True, 
        activa=True
    )
    
    # Verificar que el usuario puede acceder a esta lección
    # (opcional: implementar lógica de desbloqueo)
    
    # Obtener lecciones anterior y siguiente
    leccion_anterior = Leccion.objects.filter(
        modulo=leccion.modulo,
        orden__lt=leccion.orden,
        visible=True,
        activa=True
    ).order_by('-orden').first()
    
    leccion_siguiente = Leccion.objects.filter(
        modulo=leccion.modulo,
        orden__gt=leccion.orden,
        visible=True,
        activa=True
    ).order_by('orden').first()
    
    # Obtener o crear progreso
    progreso, created = ProgresoUsuario.objects.get_or_create(
        usuario=request.user,
        leccion=leccion,
        defaults={'intentos': 1}
    )
    
    if not created:
        progreso.intentos += 1
        progreso.save()
    
    context = {
        'leccion': leccion,
        'leccion_anterior': leccion_anterior,
        'leccion_siguiente': leccion_siguiente,
        'progreso': progreso,
    }
    
    return render(request, 'empresa/aprendizaje/leccion_interactiva.html', context)

@login_required
@require_POST
def marcar_leccion_completada(request, leccion_id):
    """Marca una lección como completada y otorga XP"""
    
    leccion = get_object_or_404(Leccion, id=leccion_id)
    
    # Obtener o crear progreso
    progreso, created = ProgresoUsuario.objects.get_or_create(
        usuario=request.user,
        leccion=leccion
    )
    
    if not progreso.completada:
        # Marcar como completada
        progreso.completada = True
        progreso.puntuacion = 100  # Puntuación por defecto
        progreso.tiempo_completado = timezone.now()
        progreso.save()
        
        # Otorgar XP
        GamificacionService.otorgar_xp(
            request.user,
            leccion.puntos_xp,
            f"Lección completada: {leccion.titulo}"
        )
        
        return JsonResponse({
            'success': True,
            'xp_ganado': leccion.puntos_xp,
            'mensaje': f'¡Lección completada! +{leccion.puntos_xp} XP'
        })
    
    return JsonResponse({
        'success': False,
        'mensaje': 'Lección ya completada'
    })

@login_required
@require_POST
def marcar_paso_completado(request, leccion_id, paso_index):
    """Marca un paso específico como completado"""
    
    leccion = get_object_or_404(Leccion, id=leccion_id)
    
    from empresa.models_aprendizaje import PasoCompletado
    
    # Crear o obtener paso completado
    paso_completado, created = PasoCompletado.objects.get_or_create(
        usuario=request.user,
        leccion=leccion,
        paso_index=paso_index
    )
    
    if created:
        # Otorgar micro-XP por paso
        micro_xp = max(1, leccion.puntos_xp // len(leccion.pasos or []))
        GamificacionService.otorgar_xp(
            request.user,
            micro_xp,
            f"Paso completado: {leccion.titulo}"
        )
        
        return JsonResponse({
            'success': True,
            'xp_ganado': micro_xp
        })
    
    return JsonResponse({
        'success': False,
        'mensaje': 'Paso ya completado'
    })

@login_required
def modulo_detalle(request, modulo_id):
    """Vista de detalle de un módulo con sus lecciones"""
    
    modulo = get_object_or_404(
        ModuloAprendizaje,
        id=modulo_id,
        visible=True,
        activo=True
    )
    
    # Obtener lecciones del módulo
    lecciones = modulo.lecciones.filter(
        visible=True,
        activa=True
    ).order_by('orden')
    
    # Obtener progreso del usuario
    progreso_usuario = ProgresoUsuario.objects.filter(
        usuario=request.user,
        leccion__in=lecciones
    ).select_related('leccion')
    
    progreso_dict = {p.leccion_id: p for p in progreso_usuario}
    
    # Calcular estadísticas del módulo
    total_lecciones = lecciones.count()
    lecciones_completadas = len([p for p in progreso_usuario if p.completada])
    porcentaje_completado = (lecciones_completadas / total_lecciones * 100) if total_lecciones > 0 else 0
    
    context = {
        'modulo': modulo,
        'lecciones': lecciones,
        'progreso_dict': progreso_dict,
        'total_lecciones': total_lecciones,
        'lecciones_completadas': lecciones_completadas,
        'porcentaje_completado': porcentaje_completado,
    }
    
    return render(request, 'empresa/aprendizaje/modulo_detalle.html', context)

@login_required
def perfil_aprendizaje(request):
    """Vista del perfil de aprendizaje del usuario"""
    
    perfil, created = PerfilAprendizaje.objects.get_or_create(usuario=request.user)
    
    # Obtener estadísticas
    total_lecciones_completadas = ProgresoUsuario.objects.filter(
        usuario=request.user,
        completada=True
    ).count()
    
    # Obtener progreso reciente
    progreso_reciente = ProgresoUsuario.objects.filter(
        usuario=request.user,
        completada=True
    ).select_related('leccion').order_by('-tiempo_completado')[:10]
    
    # Calcular racha actual
    from datetime import date, timedelta
    hoy = date.today()
    racha_actual = 0
    
    # Lógica simple de racha (se puede mejorar)
    if perfil.ultima_actividad == hoy:
        racha_actual = perfil.racha_dias
    elif perfil.ultima_actividad == hoy - timedelta(days=1):
        racha_actual = perfil.racha_dias
    else:
        racha_actual = 0
    
    context = {
        'perfil': perfil,
        'total_lecciones_completadas': total_lecciones_completadas,
        'progreso_reciente': progreso_reciente,
        'racha_actual': racha_actual,
    }
    
    return render(request, 'empresa/aprendizaje/perfil.html', context)