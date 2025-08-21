from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, ProgresoUsuario, PerfilAprendizaje
from empresa.models_aprendizaje import PasoCompletado
from django.db import transaction, IntegrityError
from empresa.services.gamificacion_service import GamificacionService
from empresa.services.simulacion_service import SimulacionService
from empresa.services.recomendacion_service import RecomendacionService
from empresa.services.social_service import SocialService
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario, EscenarioSimulacion
import json

@login_required
def dashboard_aprendizaje(request):
    """Dashboard principal del sistema de aprendizaje"""
    # Crear perfil básico si no existe
    perfil, created = PerfilAprendizaje.objects.get_or_create(
        usuario=request.user,
        defaults={'xp_total': 0, 'nivel': 1}
    )
    
    # Obtener módulos básicos
    tipo_empresa = 'comercial'
    if hasattr(request.user, 'empresa') and request.user.empresa:
        tipo_empresa = getattr(request.user.empresa, 'categoria', 'comercial')
    
    modulos = ModuloAprendizaje.objects.filter(
        tipo_empresa=tipo_empresa,
        activo=True
    ).order_by('orden')
    
    # Progreso básico
    for modulo in modulos:
        modulo.progreso = {
            'porcentaje': 0,
            'completadas': 0,
            'total': 1,
            'desbloqueado': True
        }
    
    context = {
        'perfil': perfil,
        'modulos': modulos,
        'tipo_empresa': tipo_empresa,
        'estadisticas': {'perfil': perfil},
        'recomendaciones': None,
    }
    
    return render(request, 'empresa/aprendizaje/dashboard_simple.html', context)

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
    # Adjuntar progreso a cada leccion y exponer un dict para templates
    for leccion in lecciones:
        leccion.progreso = progreso_lecciones.get(leccion.id, {'completada': False, 'puntuacion': 0, 'intentos': 0})
    progreso_lecciones_by_id = progreso_lecciones
    
    context = {
        'modulo': modulo,
        'lecciones': lecciones,
    'progreso_lecciones': progreso_lecciones,
    'progreso_lecciones_by_id': progreso_lecciones_by_id,
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
    # Parse pasos JSON si existe
    pasos_data = None
    try:
        if hasattr(leccion, 'pasos') and leccion.pasos:
            # If pasos is stored as TextField (string), try to parse
            if isinstance(leccion.pasos, str):
                import json
                pasos_data = json.loads(leccion.pasos)
            else:
                pasos_data = leccion.pasos
    except Exception:
        pasos_data = None

    context['leccion_pasos'] = pasos_data
    # Serializar para inyección segura en JS
    try:
        import json
        context['leccion_pasos_json'] = json.dumps(pasos_data) if pasos_data is not None else 'null'
        context['leccion_contenido_js'] = json.dumps(leccion.contenido or '')
    except Exception:
        context['leccion_pasos_json'] = 'null'
        context['leccion_contenido_js'] = json.dumps(leccion.contenido or '')

    # Use interactive template for practice lessons
    if leccion.tipo == 'practica':
        return render(request, 'empresa/aprendizaje/leccion_interactiva.html', context)
    else:
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
def paso_completado(request):
    """Registra la finalización de un micro-paso dentro de una lección y otorga micro-XP.
    Previene doble conteo usando la sesión del usuario.
    Espera JSON: { leccion_id: int, paso_index: int, micro_xp: int (opcional) }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST.dict()
    except Exception:
        data = request.POST.dict()

    leccion_id = data.get('leccion_id') or data.get('leccion')
    paso_index = data.get('paso_index')
    micro_xp = data.get('micro_xp')

    if not leccion_id:
        return JsonResponse({'error': 'leccion_id required'}, status=400)

    try:
        leccion = Leccion.objects.get(id=leccion_id)
    except Leccion.DoesNotExist:
        return JsonResponse({'error': 'Lección no encontrada'}, status=404)

    progreso, created = ProgresoUsuario.objects.get_or_create(usuario=request.user, leccion=leccion)

    # Normalizar paso_index
    try:
        paso_index = int(paso_index) if paso_index is not None else None
    except Exception:
        paso_index = None

    # Validar paso_index si la lección define pasos
    try:
        pasos_raw = getattr(leccion, 'pasos', None)
        pasos_list = None
        if pasos_raw:
            if isinstance(pasos_raw, str):
                import json as _json
                pasos_list = _json.loads(pasos_raw)
            else:
                pasos_list = pasos_raw

            if paso_index is not None and (paso_index < 0 or paso_index >= len(pasos_list)):
                return JsonResponse({'error': 'paso_index fuera de rango'}, status=400)
    except Exception:
        # Si ocurre algún error parsing pasos, no bloquear pero no validar rango
        pasos_list = None

    # Evitar doble conteo: preferimos persistir en DB con unique constraint
    try:
        micro_xp = int(micro_xp) if micro_xp is not None else 5
    except Exception:
        micro_xp = 5

    created_paso = False
    try:
        with transaction.atomic():
            paso_obj, created_paso = PasoCompletado.objects.get_or_create(
                usuario=request.user,
                leccion=leccion,
                paso_index=paso_index
            )
    except IntegrityError:
        created_paso = False

    if not created_paso:
        # Fallback: check session to avoid double response
        session_key = f'aprendizaje_paso_{leccion.id}_{paso_index}'
        if request.session.get(session_key):
            perfil = GamificacionService.obtener_estadisticas_usuario(request.user)['perfil']
            return JsonResponse({'ok': False, 'message': 'Paso ya registrado', 'xp_total': perfil.xp_total})
        # mark session anyway
        request.session[session_key] = True
        perfil = GamificacionService.obtener_estadisticas_usuario(request.user)['perfil']
        return JsonResponse({'ok': False, 'message': 'Paso ya registrado', 'xp_total': perfil.xp_total})

    # Otorgar micro-XP
    resultado = GamificacionService.otorgar_xp(request.user, micro_xp, f"Paso completado: {leccion.titulo}")

    # Actualizar conteo simple en progreso (usar intentos como contador de pasos completados)
    try:
        progreso.intentos = (progreso.intentos or 0) + 1
        progreso.save()
    except Exception:
        pass

    # Marcar en sesión
    request.session[f'aprendizaje_paso_{leccion.id}_{paso_index}'] = True

    return JsonResponse({'ok': True, 'resultado': resultado, 'intentos': progreso.intentos})


@login_required
def simulacion_escenarios_api(request):
    """API que devuelve los escenarios activos para un TipoSimulacion dado.
    Query params: tipo_id (int)
    """
    tipo_id = request.GET.get('tipo_id')
    if not tipo_id:
        return JsonResponse({'error': 'tipo_id requerido'}, status=400)

    try:
        tipo = TipoSimulacion.objects.get(id=tipo_id, activo=True)
    except TipoSimulacion.DoesNotExist:
        return JsonResponse({'error': 'Tipo de simulación no encontrado'}, status=404)

    escenarios = EscenarioSimulacion.objects.filter(tipo_simulacion=tipo, activo=True).order_by('dificultad', 'nombre')
    data = []
    for e in escenarios:
        data.append({
            'id': e.id,
            'nombre': e.nombre,
            'descripcion': e.descripcion,
            'datos_iniciales': e.datos_iniciales,
            'puntos_max': e.puntos_max,
            'dificultad': e.dificultad,
        })

    return JsonResponse({'ok': True, 'escenarios': data})


@login_required
def simulacion_start_api(request):
    """Inicia una simulación desde la UI (sandbox).
    Espera JSON: { tipo_id: int, escenario_id: int (opcional), leccion_id: int (opcional) }
    Devuelve: { ok: True, simulacion_id: int, datos_iniciales: dict }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST.dict()
    except Exception:
        data = request.POST.dict()

    tipo_id = data.get('tipo_id') or data.get('tipo')
    escenario_id = data.get('escenario_id')
    leccion_id = data.get('leccion_id')

    if not tipo_id:
        return JsonResponse({'error': 'tipo_id requerido'}, status=400)

    # Resolver lección si se proporcionó
    leccion = None
    if leccion_id:
        try:
            leccion = Leccion.objects.get(id=leccion_id)
        except Leccion.DoesNotExist:
            leccion = None

    try:
        tipo = TipoSimulacion.objects.get(id=tipo_id, activo=True)
    except TipoSimulacion.DoesNotExist:
        return JsonResponse({'error': 'Tipo de simulación no encontrado'}, status=404)

    # Iniciar simulación (modo sandbox para prácticas desde la Academia)
    simulacion = SimulacionService.iniciar_simulacion(request.user, tipo.id, leccion, modo_sandbox=True)

    datos_iniciales = {}
    if escenario_id:
        try:
            escenario = EscenarioSimulacion.objects.get(id=escenario_id, tipo_simulacion=tipo, activo=True)
            datos_iniciales = escenario.datos_iniciales or {}
            # Guardar los datos iniciales en la simulación
            simulacion.datos_entrada = datos_iniciales
            simulacion.save()
        except EscenarioSimulacion.DoesNotExist:
            pass

    return JsonResponse({'ok': True, 'simulacion_id': simulacion.id, 'datos_iniciales': datos_iniciales})


@login_required
def simulacion_tipos_api(request):
    """Devuelve los tipos de simulación activos para poblar el selector en la UI"""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=400)

    tipos = TipoSimulacion.objects.filter(activo=True).order_by('nombre')
    data = []
    for t in tipos:
        data.append({
            'id': t.id,
            'nombre': t.nombre,
            'categoria': t.categoria,
            'descripcion': t.descripcion,
            'icono': t.icono,
        })

    return JsonResponse({'ok': True, 'tipos': data})

@login_required
def simulacion_venta(request, leccion_id=None):
    """Simulación interactiva de venta"""
    leccion = None
    if leccion_id:
        leccion = get_object_or_404(Leccion, id=leccion_id)
    
    if request.method == 'POST':
        # Iniciar simulación en modo sandbox (para que los movimientos no persistan)
        tipo_simulacion = TipoSimulacion.objects.get(nombre='Simulación de Venta')
        simulacion = SimulacionService.iniciar_simulacion(
            request.user,
            tipo_simulacion.id,
            leccion,
            modo_sandbox=True
        )

        # Procesar datos en modo sandbox
        resultado = SimulacionService.procesar_simulacion_venta(simulacion, request.POST.dict(), modo_sandbox=True)
        
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
        # Iniciar simulación en modo sandbox
        tipo_simulacion = TipoSimulacion.objects.get(nombre='Simulación de Receta')
        simulacion = SimulacionService.iniciar_simulacion(
            request.user,
            tipo_simulacion.id,
            leccion,
            modo_sandbox=True
        )

        # Procesar datos en modo sandbox
        resultado = SimulacionService.procesar_simulacion_receta(simulacion, request.POST.dict(), modo_sandbox=True)
        
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
        # Iniciar simulación en modo sandbox
        tipo_simulacion = TipoSimulacion.objects.get(nombre='Simulación de Servicio')
        simulacion = SimulacionService.iniciar_simulacion(
            request.user,
            tipo_simulacion.id,
            leccion,
            modo_sandbox=True
        )

        # Procesar datos en modo sandbox
        resultado = SimulacionService.procesar_simulacion_servicio(simulacion, request.POST.dict(), modo_sandbox=True)
        
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