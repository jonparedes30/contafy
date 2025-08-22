from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from empresa.services.recomendacion_service import RecomendacionService
import json

@login_required
def obtener_recomendaciones_api(request):
    """API para obtener recomendaciones personalizadas"""
    
    recomendaciones = RecomendacionService.obtener_recomendaciones_dashboard(request.user)
    
    # Serializar la siguiente lección
    siguiente_leccion = None
    if recomendaciones['siguiente_leccion']:
        leccion = recomendaciones['siguiente_leccion']
        siguiente_leccion = {
            'id': leccion.id,
            'titulo': leccion.titulo,
            'tipo': leccion.tipo,
            'puntos_xp': leccion.puntos_xp,
            'tiempo_estimado': leccion.tiempo_estimado,
            'modulo': {
                'id': leccion.modulo.id,
                'nombre': leccion.modulo.nombre,
                'icono': leccion.modulo.icono
            }
        }
    
    return JsonResponse({
        'ok': True,
        'recomendaciones': {
            'siguiente_leccion': siguiente_leccion,
            'mensaje_motivacional': recomendaciones['mensaje_motivacional'],
            'progreso_global': recomendaciones['progreso_global'],
            'rendimiento': recomendaciones['rendimiento'],
            'sugerencias': recomendaciones['sugerencias']
        }
    })

@csrf_exempt
@login_required
def registrar_interaccion_api(request):
    """API para registrar interacciones del usuario"""
    
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'})
    
    try:
        data = json.loads(request.body.decode('utf-8'))
    except:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'})
    
    tipo_interaccion = data.get('tipo')
    datos_interaccion = data.get('datos', {})
    
    if not tipo_interaccion:
        return JsonResponse({'ok': False, 'error': 'tipo required'})
    
    # Registrar interacción
    resultado = RecomendacionService.registrar_interaccion(
        request.user,
        tipo_interaccion,
        datos_interaccion
    )
    
    return JsonResponse({
        'ok': True,
        'registrado': resultado
    })

@login_required
def obtener_siguiente_leccion_api(request):
    """API específica para obtener solo la siguiente lección recomendada"""
    
    siguiente_leccion = RecomendacionService.obtener_siguiente_leccion(request.user)
    
    if not siguiente_leccion:
        return JsonResponse({
            'ok': True,
            'siguiente_leccion': None,
            'mensaje': 'Has completado todas las lecciones disponibles. ¡Felicidades!'
        })
    
    return JsonResponse({
        'ok': True,
        'siguiente_leccion': {
            'id': siguiente_leccion.id,
            'titulo': siguiente_leccion.titulo,
            'tipo': siguiente_leccion.tipo,
            'puntos_xp': siguiente_leccion.puntos_xp,
            'tiempo_estimado': siguiente_leccion.tiempo_estimado,
            'url': f'/app-beta-2024/aprendizaje/leccion/{siguiente_leccion.id}/',
            'modulo': {
                'id': siguiente_leccion.modulo.id,
                'nombre': siguiente_leccion.modulo.nombre,
                'icono': siguiente_leccion.modulo.icono
            }
        }
    })