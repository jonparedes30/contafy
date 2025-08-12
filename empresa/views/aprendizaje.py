from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, ProgresoUsuario, PerfilAprendizaje
from empresa.services.gamificacion_service import GamificacionService
from empresa.services.simulacion_service import SimulacionService
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario

@login_required
def dashboard_aprendizaje(request):
    """Dashboard principal del sistema de aprendizaje"""
    usuario = request.user
    
    # Obtener estadísticas completas del usuario
    estadisticas = GamificacionService.obtener_estadisticas_usuario(usuario)
    perfil = estadisticas['perfil']
    
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
        'estadisticas': estadisticas,
    }
    
    return render(request, 'empresa/aprendizaje/dashboard.html', context)

@login_required
def modulo_detalle(request, modulo_id):
    """Detalle de un módulo específico"""
    modulo = get_object_or_404(ModuloAprendizaje, id=modulo_id, activo=True)
    
    # Verificar que el módulo corresponde al tipo de empresa del usuario
    usuario = request.user
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
            
            # Usar servicio de gamificación
            resultado = GamificacionService.otorgar_xp(
                request.user, 
                leccion.puntos_xp, 
                f"Lección completada: {leccion.titulo}"
            )
            
            # Registrar actividad (1 lección completada)
            GamificacionService.registrar_actividad_diaria(
                request.user, 
                lecciones=1, 
                tiempo_minutos=leccion.tiempo_estimado
            )
            
            # Mensajes de éxito
            if resultado['subio_nivel']:
                messages.success(request, f'¡Felicidades! Has subido al nivel {resultado["nivel_actual"]}!')
            
            messages.success(request, f'¡Lección completada! +{leccion.puntos_xp} XP')
            
            # Verificar si se desbloquearon logros
            logros_nuevos = GamificacionService.verificar_logros(request.user)
            for logro_usuario in logros_nuevos:
                messages.success(request, f'🏆 ¡Nuevo logro desbloqueado: {logro_usuario.logro.nombre}!')
            
            return redirect('empresa:aprendizaje_modulo', modulo_id=leccion.modulo.id)
    
    context = {
        'leccion': leccion,
        'progreso': progreso,
    }
    
    return render(request, 'empresa/aprendizaje/leccion_detalle.html', context)

@login_required
def perfil_usuario(request):
    """Perfil del usuario con estadísticas de gamificación"""
    estadisticas = GamificacionService.obtener_estadisticas_usuario(request.user)
    
    context = {
        'estadisticas': estadisticas,
    }
    
    return render(request, 'empresa/aprendizaje/perfil_usuario.html', context)

@login_required
def simulacion_venta(request, leccion_id=None):
    """Simulación interactiva de venta"""
    leccion = None
    if leccion_id:
        leccion = get_object_or_404(Leccion, id=leccion_id)
    
    if request.method == 'POST':
        # Iniciar simulación
        tipo_simulacion = TipoSimulacion.objects.get(nombre='Simulación de Venta')
        simulacion = SimulacionService.iniciar_simulacion(
            request.user, 
            tipo_simulacion.id, 
            leccion
        )
        
        # Procesar datos
        resultado = SimulacionService.procesar_simulacion_venta(simulacion, request.POST.dict())
        
        return JsonResponse(resultado)
    
    # Datos de ejemplo para la simulación
    productos_ejemplo = [
        {'nombre': 'Camiseta', 'precio': 15.00},
        {'nombre': 'Pantalón', 'precio': 25.00},
        {'nombre': 'Zapatos', 'precio': 45.00},
    ]
    
    context = {
        'leccion': leccion,
        'productos_ejemplo': productos_ejemplo,
    }
    
    return render(request, 'empresa/aprendizaje/simulacion_venta.html', context)

@login_required
def simulacion_receta(request, leccion_id=None):
    """Simulación interactiva de receta de producción"""
    leccion = None
    if leccion_id:
        leccion = get_object_or_404(Leccion, id=leccion_id)
    
    if request.method == 'POST':
        # Iniciar simulación
        tipo_simulacion = TipoSimulacion.objects.get(nombre='Simulación de Receta')
        simulacion = SimulacionService.iniciar_simulacion(
            request.user, 
            tipo_simulacion.id, 
            leccion
        )
        
        # Procesar datos
        resultado = SimulacionService.procesar_simulacion_receta(simulacion, request.POST.dict())
        
        return JsonResponse(resultado)
    
    # Ingredientes de ejemplo
    ingredientes_ejemplo = [
        {'nombre': 'Harina', 'unidad': 'kg', 'precio': 1.50},
        {'nombre': 'Azúcar', 'unidad': 'kg', 'precio': 2.00},
        {'nombre': 'Huevos', 'unidad': 'unidad', 'precio': 0.25},
        {'nombre': 'Mantequilla', 'unidad': 'kg', 'precio': 4.00},
    ]
    
    context = {
        'leccion': leccion,
        'ingredientes_ejemplo': ingredientes_ejemplo,
    }
    
    return render(request, 'empresa/aprendizaje/simulacion_receta.html', context)

@login_required
def simulacion_servicio(request, leccion_id=None):
    """Simulación interactiva de facturación de servicio"""
    leccion = None
    if leccion_id:
        leccion = get_object_or_404(Leccion, id=leccion_id)
    
    if request.method == 'POST':
        # Iniciar simulación
        tipo_simulacion = TipoSimulacion.objects.get(nombre='Simulación de Servicio')
        simulacion = SimulacionService.iniciar_simulacion(
            request.user, 
            tipo_simulacion.id, 
            leccion
        )
        
        # Procesar datos
        resultado = SimulacionService.procesar_simulacion_servicio(simulacion, request.POST.dict())
        
        return JsonResponse(resultado)
    
    # Tipos de servicio de ejemplo
    servicios_ejemplo = [
        {'nombre': 'Consultoría', 'tarifa_sugerida': 25.00},
        {'nombre': 'Diseño Gráfico', 'tarifa_sugerida': 20.00},
        {'nombre': 'Reparación', 'tarifa_sugerida': 15.00},
    ]
    
    context = {
        'leccion': leccion,
        'servicios_ejemplo': servicios_ejemplo,
    }
    
    return render(request, 'empresa/aprendizaje/simulacion_servicio.html', context)