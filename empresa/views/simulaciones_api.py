from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from empresa.models_simulaciones import TipoSimulacion, EscenarioSimulacion, SimulacionUsuario
from empresa.services.simulacion_service import SimulacionService
import json

@login_required
def simulacion_tipos_api(request):
    """API para obtener tipos de simulación disponibles"""
    tipos = TipoSimulacion.objects.filter(activo=True)
    data = [{
        'id': t.id,
        'nombre': t.nombre,
        'categoria': t.categoria,
        'descripcion': t.descripcion
    } for t in tipos]
    
    return JsonResponse({'ok': True, 'tipos': data})

@login_required
def simulacion_escenarios_api(request):
    """API para obtener escenarios de un tipo específico"""
    tipo_id = request.GET.get('tipo_id')
    if not tipo_id:
        return JsonResponse({'ok': False, 'error': 'tipo_id required'})
    
    try:
        tipo = TipoSimulacion.objects.get(id=tipo_id, activo=True)
        escenarios = EscenarioSimulacion.objects.filter(tipo_simulacion=tipo, activo=True)
        data = [{
            'id': e.id,
            'nombre': e.nombre,
            'descripcion': e.descripcion,
            'dificultad': e.dificultad
        } for e in escenarios]
        
        return JsonResponse({'ok': True, 'escenarios': data})
    except TipoSimulacion.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Tipo no encontrado'})

@csrf_exempt
@login_required
def simulacion_start_api(request):
    """API para iniciar una simulación sandbox"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'})
    
    try:
        data = json.loads(request.body.decode('utf-8'))
    except:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'})
    
    tipo_id = data.get('tipo_id')
    escenario_id = data.get('escenario_id')
    leccion_id = data.get('leccion_id')
    
    if not tipo_id:
        return JsonResponse({'ok': False, 'error': 'tipo_id required'})
    
    try:
        tipo = TipoSimulacion.objects.get(id=tipo_id, activo=True)
        escenario = None
        
        if escenario_id:
            escenario = EscenarioSimulacion.objects.get(id=escenario_id, activo=True)
        
        # Crear simulación sandbox
        simulacion = SimulacionUsuario.objects.create(
            usuario=request.user,
            tipo_simulacion=tipo,
            escenario=escenario,
            es_sandbox=True,
            datos_entrada=escenario.datos_iniciales if escenario else {},
            estado='iniciada'
        )
        
        return JsonResponse({
            'ok': True,
            'simulacion_id': simulacion.id,
            'datos_iniciales': simulacion.datos_entrada,
            'tipo': tipo.categoria
        })
        
    except (TipoSimulacion.DoesNotExist, EscenarioSimulacion.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'Tipo o escenario no encontrado'})

@csrf_exempt
@login_required
def simulacion_step_api(request, simulacion_id):
    """API para procesar un paso de simulación"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'})
    
    try:
        data = json.loads(request.body.decode('utf-8'))
    except:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'})
    
    try:
        simulacion = SimulacionUsuario.objects.get(
            id=simulacion_id, 
            usuario=request.user,
            es_sandbox=True
        )
        
        # Procesar paso usando SimulacionService
        resultado = SimulacionService.procesar_paso_simulacion(
            simulacion, 
            data.get('accion'),
            data.get('datos', {})
        )
        
        return JsonResponse({
            'ok': True,
            'resultado': resultado,
            'estado': simulacion.estado,
            'puntuacion': simulacion.puntuacion_obtenida
        })
        
    except SimulacionUsuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Simulación no encontrada'})

@login_required
def simulacion_result_api(request, simulacion_id):
    """API para obtener resultado final de simulación"""
    try:
        simulacion = SimulacionUsuario.objects.get(
            id=simulacion_id,
            usuario=request.user
        )
        
        return JsonResponse({
            'ok': True,
            'simulacion': {
                'id': simulacion.id,
                'estado': simulacion.estado,
                'puntuacion': simulacion.puntuacion_obtenida,
                'feedback': simulacion.feedback,
                'completada_en': simulacion.completada_en.isoformat() if simulacion.completada_en else None
            }
        })
        
    except SimulacionUsuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Simulación no encontrada'})