from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q
from empresa.services.social_service import SocialService
from empresa.models_social import LigaSemanal, RetoSocial, LogroCompartido
from empresa.models_gamificacion import LogroUsuario
import json

@login_required
def dashboard_social(request):
    """Dashboard social de la academia"""
    # Crear liga semanal si no existe
    liga_actual = SocialService.crear_liga_semanal()
    
    # Obtener tabla de clasificación
    clasificacion = SocialService.obtener_tabla_clasificacion(liga_actual, limite=10)
    
    # Obtener retos activos del usuario
    retos_activos = RetoSocial.objects.filter(
        Q(creador=request.user) | Q(retado=request.user),
        activo=True
    ).select_related('creador', 'retado')
    
    # Verificar progreso de retos
    SocialService.verificar_retos_usuario(request.user)
    
    # Obtener feed social
    feed_social = SocialService.obtener_feed_social(request.user, limite=10)
    
    # Obtener posición del usuario actual
    mi_posicion = None
    for i, participante in enumerate(clasificacion, 1):
        if participante.usuario == request.user:
            mi_posicion = i
            break
    
    context = {
        'liga_actual': liga_actual,
        'clasificacion': clasificacion,
        'mi_posicion': mi_posicion,
        'retos_activos': retos_activos,
        'feed_social': feed_social,
    }
    
    return render(request, 'empresa/aprendizaje/social_dashboard.html', context)

@login_required
def crear_reto(request):
    """Crear un nuevo reto"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else request.POST.dict()
        except:
            data = request.POST.dict()
        
        retado_id = data.get('retado_id')
        tipo = data.get('tipo')
        objetivo = data.get('objetivo')
        dias_limite = int(data.get('dias_limite', 7))
        
        if not all([retado_id, tipo, objetivo]):
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
        
        try:
            retado = User.objects.get(id=retado_id)
            objetivo = int(objetivo)
        except (User.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Usuario o objetivo inválido'}, status=400)
        
        if retado == request.user:
            return JsonResponse({'error': 'No puedes retarte a ti mismo'}, status=400)
        
        # Verificar que no existe un reto activo entre estos usuarios del mismo tipo
        reto_existente = RetoSocial.objects.filter(
            Q(creador=request.user, retado=retado) | Q(creador=retado, retado=request.user),
            tipo=tipo,
            activo=True
        ).exists()
        
        if reto_existente:
            return JsonResponse({'error': 'Ya existe un reto activo de este tipo entre ustedes'}, status=400)
        
        reto = SocialService.crear_reto(request.user, retado, tipo, objetivo, dias_limite)
        
        return JsonResponse({
            'ok': True,
            'reto_id': reto.id,
            'mensaje': f'Reto creado exitosamente con {retado.get_full_name() or retado.username}'
        })
    
    # GET: mostrar formulario
    # Obtener usuarios de la misma empresa para retar
    usuarios_disponibles = User.objects.filter(
        is_active=True,
        empresa=request.user.empresa
    ).exclude(id=request.user.id).select_related('perfilaprendizaje')
    
    context = {
        'usuarios_disponibles': usuarios_disponibles,
        'tipos_reto': RetoSocial.TIPOS,
    }
    
    return render(request, 'empresa/aprendizaje/crear_reto.html', context)

@login_required
def compartir_logro(request):
    """Compartir un logro en el feed social"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else request.POST.dict()
        except:
            data = request.POST.dict()
        
        logro_usuario_id = data.get('logro_usuario_id')
        mensaje = data.get('mensaje', '')
        
        if not logro_usuario_id:
            return JsonResponse({'error': 'logro_usuario_id requerido'}, status=400)
        
        try:
            logro_usuario = LogroUsuario.objects.get(
                id=logro_usuario_id,
                usuario=request.user
            )
        except LogroUsuario.DoesNotExist:
            return JsonResponse({'error': 'Logro no encontrado'}, status=404)
        
        # Verificar que no se haya compartido ya
        if LogroCompartido.objects.filter(
            usuario=request.user,
            logro_usuario=logro_usuario
        ).exists():
            return JsonResponse({'error': 'Este logro ya fue compartido'}, status=400)
        
        logro_compartido = SocialService.compartir_logro(request.user, logro_usuario, mensaje)
        
        return JsonResponse({
            'ok': True,
            'logro_compartido_id': logro_compartido.id,
            'mensaje': 'Logro compartido exitosamente'
        })
    
    return JsonResponse({'error': 'POST required'}, status=400)

@login_required
def toggle_like_logro(request):
    """Dar o quitar like a un logro compartido"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else request.POST.dict()
        except:
            data = request.POST.dict()
        
        logro_compartido_id = data.get('logro_compartido_id')
        
        if not logro_compartido_id:
            return JsonResponse({'error': 'logro_compartido_id requerido'}, status=400)
        
        try:
            logro_compartido = LogroCompartido.objects.get(id=logro_compartido_id)
        except LogroCompartido.DoesNotExist:
            return JsonResponse({'error': 'Logro compartido no encontrado'}, status=404)
        
        # Toggle like
        if request.user in logro_compartido.likes.all():
            SocialService.quitar_like_logro(request.user, logro_compartido)
            liked = False
        else:
            SocialService.dar_like_logro(request.user, logro_compartido)
            liked = True
        
        return JsonResponse({
            'ok': True,
            'liked': liked,
            'total_likes': logro_compartido.likes.count()
        })
    
    return JsonResponse({'error': 'POST required'}, status=400)

@login_required
def clasificacion_completa(request):
    """Ver la clasificación completa de la liga actual"""
    liga_actual = LigaSemanal.objects.filter(activa=True).first()
    
    if not liga_actual:
        messages.info(request, 'No hay una liga activa en este momento.')
        return redirect('empresa:social_dashboard')
    
    clasificacion = SocialService.obtener_tabla_clasificacion(liga_actual, limite=100)
    
    context = {
        'liga_actual': liga_actual,
        'clasificacion': clasificacion,
    }
    
    return render(request, 'empresa/aprendizaje/clasificacion_completa.html', context)

@login_required
def mis_retos(request):
    """Ver todos los retos del usuario (activos e históricos)"""
    retos_activos = RetoSocial.objects.filter(
        Q(creador=request.user) | Q(retado=request.user),
        activo=True
    ).select_related('creador', 'retado').order_by('-id')
    
    retos_completados = RetoSocial.objects.filter(
        Q(creador=request.user) | Q(retado=request.user),
        activo=False
    ).select_related('creador', 'retado', 'ganador').order_by('-id')[:20]
    
    # Verificar progreso de retos activos
    SocialService.verificar_retos_usuario(request.user)
    
    context = {
        'retos_activos': retos_activos,
        'retos_completados': retos_completados,
    }
    
    return render(request, 'empresa/aprendizaje/mis_retos.html', context)

@login_required
def feed_social(request):
    """Feed completo de logros compartidos"""
    feed = SocialService.obtener_feed_social(request.user, limite=50)
    
    context = {
        'feed_social': feed,
    }
    
    return render(request, 'empresa/aprendizaje/feed_social.html', context)