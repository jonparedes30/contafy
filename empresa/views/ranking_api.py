from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from empresa.services.gamificacion_service import GamificacionService
from empresa.models_gamificacion import Liga, ParticipacionLiga, Reto, ParticipacionReto
from datetime import datetime

@login_required
def ranking_semanal_api(request):
    """API para obtener el ranking semanal"""
    
    tipo_empresa = request.GET.get('tipo_empresa')
    limite = int(request.GET.get('limite', 10))
    
    # Si no se especifica tipo, usar el del usuario
    if not tipo_empresa and request.user.empresa:
        tipo_empresa = request.user.empresa.categoria
    
    ranking = GamificacionService.obtener_ranking_semanal(tipo_empresa, limite)
    
    # Encontrar posición del usuario actual
    posicion_usuario = None
    for i, entrada in enumerate(ranking, 1):
        if entrada['usuario__id'] == request.user.id:
            posicion_usuario = i
            break
    
    return JsonResponse({
        'ok': True,
        'ranking': ranking,
        'posicion_usuario': posicion_usuario,
        'total_participantes': len(ranking)
    })

@login_required
def ligas_activas_api(request):
    """API para obtener ligas activas"""
    
    ligas_activas = Liga.objects.filter(
        activa=True,
        fecha_inicio__lte=datetime.now(),
        fecha_fin__gte=datetime.now()
    )
    
    ligas_data = []
    for liga in ligas_activas:
        # Obtener participación del usuario
        participacion_usuario = ParticipacionLiga.objects.filter(
            usuario=request.user,
            liga=liga
        ).first()
        
        # Top 3 de la liga
        top_participantes = ParticipacionLiga.objects.filter(
            liga=liga
        ).select_related('usuario').order_by('-puntos_obtenidos')[:3]
        
        ligas_data.append({
            'id': liga.id,
            'nombre': liga.nombre,
            'tipo': liga.tipo,
            'premio_xp': liga.premio_xp,
            'fecha_fin': liga.fecha_fin.isoformat(),
            'participacion_usuario': {
                'puntos': participacion_usuario.puntos_obtenidos if participacion_usuario else 0,
                'posicion': participacion_usuario.posicion if participacion_usuario else 0,
                'inscrito': bool(participacion_usuario)
            },
            'top_participantes': [{
                'username': p.usuario.username,
                'puntos': p.puntos_obtenidos,
                'posicion': p.posicion
            } for p in top_participantes]
        })
    
    return JsonResponse({
        'ok': True,
        'ligas': ligas_data
    })

@login_required
def inscribir_liga_api(request, liga_id):
    """API para inscribirse en una liga"""
    
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'})
    
    try:
        liga = Liga.objects.get(id=liga_id, activa=True)
        
        # Verificar que la liga esté activa
        if liga.fecha_fin < datetime.now():
            return JsonResponse({'ok': False, 'error': 'Liga ya finalizada'})
        
        participacion, created = ParticipacionLiga.objects.get_or_create(
            usuario=request.user,
            liga=liga
        )
        
        return JsonResponse({
            'ok': True,
            'inscrito': True,
            'nueva_inscripcion': created
        })
        
    except Liga.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Liga no encontrada'})

@login_required
def retos_activos_api(request):
    """API para obtener retos activos"""
    
    retos_activos = Reto.objects.filter(
        activo=True,
        fecha_inicio__lte=datetime.now(),
        fecha_fin__gte=datetime.now()
    )
    
    retos_data = []
    for reto in retos_activos:
        # Obtener participación del usuario
        participacion = ParticipacionReto.objects.filter(
            usuario=request.user,
            reto=reto
        ).first()
        
        import json
        try:
            objetivo = json.loads(reto.objetivo)
            progreso_usuario = json.loads(participacion.progreso) if participacion and participacion.progreso else {}
        except:
            objetivo = {'tipo': 'lecciones', 'cantidad': 5}
            progreso_usuario = {}
        
        retos_data.append({
            'id': reto.id,
            'nombre': reto.nombre,
            'descripcion': reto.descripcion,
            'objetivo': objetivo,
            'premio_xp': reto.premio_xp,
            'fecha_fin': reto.fecha_fin.isoformat(),
            'participacion_usuario': {
                'inscrito': bool(participacion),
                'completado': participacion.completado if participacion else False,
                'progreso': progreso_usuario
            }
        })
    
    return JsonResponse({
        'ok': True,
        'retos': retos_data
    })

@login_required
def ranking_view(request):
    """Vista del ranking y ligas"""
    
    # Obtener estadísticas del usuario
    estadisticas = GamificacionService.obtener_estadisticas_usuario(request.user)
    
    # Crear liga semanal si no existe
    liga_semanal = GamificacionService.crear_liga_semanal()
    
    context = {
        'estadisticas': estadisticas,
        'liga_semanal': liga_semanal
    }
    
    return render(request, 'empresa/aprendizaje/ranking.html', context)