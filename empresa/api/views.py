from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, ProgresoUsuario
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario, EscenarioSimulacion
from empresa.services.simulacion_service import SimulacionService
from empresa.services.recommendation_service import RecommendationService
from .serializers import (
    ModuloAprendizajeSerializer, LeccionSerializer, SimulacionUsuarioSerializer,
    SimulacionCreateSerializer, SimulacionGuardarSerializer, ProgresoUsuarioSerializer,
    RecomendacionSerializer, EscenarioSimulacionSerializer
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def modulos_list(request):
    """Lista módulos filtrados por tipo de empresa del usuario"""
    tipo_empresa = request.GET.get('tipo_empresa', 'comercial')
    
    modulos = ModuloAprendizaje.objects.filter(
        tipo_empresa=tipo_empresa,
        visible=True,
        activo=True
    ).order_by('orden')
    
    serializer = ModuloAprendizajeSerializer(modulos, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lecciones_list(request):
    """Lista lecciones filtradas por módulo y tipo de empresa"""
    modulo_id = request.GET.get('modulo_id')
    tipo_empresa = request.GET.get('tipo_empresa', 'comercial')
    
    queryset = Leccion.objects.filter(visible=True, activa=True)
    
    if modulo_id:
        queryset = queryset.filter(modulo_id=modulo_id)
    else:
        queryset = queryset.filter(modulo__tipo_empresa=tipo_empresa)
    
    lecciones = queryset.select_related('modulo').order_by('modulo__orden', 'orden')
    serializer = LeccionSerializer(lecciones, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leccion_detail(request, leccion_id):
    """Detalle de una lección específica"""
    leccion = get_object_or_404(Leccion, id=leccion_id, visible=True, activa=True)
    serializer = LeccionSerializer(leccion)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulacion_start(request):
    """Inicia una nueva simulación"""
    serializer = SimulacionCreateSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        
        leccion = None
        if data.get('leccion_id'):
            leccion = get_object_or_404(Leccion, id=data['leccion_id'])
        
        simulacion = SimulacionService.iniciar_simulacion(
            usuario=request.user,
            tipo_simulacion_id=data['tipo_simulacion_id'],
            leccion=leccion,
            modo_sandbox=data.get('modo_sandbox', True)
        )
        
        # Asignar escenario si se especifica
        if data.get('escenario_id'):
            escenario = get_object_or_404(EscenarioSimulacion, id=data['escenario_id'])
            simulacion.escenario = escenario
            simulacion.save()
        
        response_serializer = SimulacionUsuarioSerializer(simulacion)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def simulacion_detail(request, simulacion_id):
    """Obtiene el estado actual de una simulación"""
    simulacion = get_object_or_404(
        SimulacionUsuario, 
        id=simulacion_id, 
        usuario=request.user
    )
    serializer = SimulacionUsuarioSerializer(simulacion)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulacion_guardar(request, simulacion_id):
    """Guarda el progreso intermedio de una simulación"""
    simulacion = get_object_or_404(
        SimulacionUsuario, 
        id=simulacion_id, 
        usuario=request.user
    )
    
    serializer = SimulacionGuardarSerializer(data=request.data)
    if serializer.is_valid():
        # Guardar datos intermedios sin procesar
        simulacion.datos_entrada = serializer.validated_data['datos_usuario']
        simulacion.save()
        
        return Response({'status': 'guardado'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulacion_finalizar(request, simulacion_id):
    """Finaliza y procesa una simulación"""
    simulacion = get_object_or_404(
        SimulacionUsuario, 
        id=simulacion_id, 
        usuario=request.user
    )
    
    serializer = SimulacionGuardarSerializer(data=request.data)
    if serializer.is_valid():
        datos_usuario = serializer.validated_data['datos_usuario']
        
        # Procesar según tipo de simulación
        if simulacion.tipo_simulacion.categoria == 'comercial':
            resultado = SimulacionService.procesar_simulacion_venta(
                simulacion, datos_usuario, modo_sandbox=simulacion.es_sandbox
            )
        elif simulacion.tipo_simulacion.categoria == 'manufactura':
            resultado = SimulacionService.procesar_simulacion_receta(
                simulacion, datos_usuario, modo_sandbox=simulacion.es_sandbox
            )
        elif simulacion.tipo_simulacion.categoria == 'servicios':
            resultado = SimulacionService.procesar_simulacion_servicio(
                simulacion, datos_usuario, modo_sandbox=simulacion.es_sandbox
            )
        else:
            return Response(
                {'error': 'Tipo de simulación no soportado'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar recomendaciones si hay lección asociada
        recomendacion = None
        if simulacion.leccion:
            recomendacion = RecommendationService.actualizar_recomendaciones_post_leccion(
                request.user, simulacion.leccion, resultado.get('puntuacion', 0)
            )
        
        response_data = {
            'resultado': resultado,
            'simulacion': SimulacionUsuarioSerializer(simulacion).data
        }
        
        if recomendacion:
            response_data['recomendacion'] = recomendacion
        
        return Response(response_data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progreso_usuario(request):
    """Obtiene el progreso del usuario"""
    tipo_empresa = request.GET.get('tipo_empresa', 'comercial')
    
    progreso = ProgresoUsuario.objects.filter(
        usuario=request.user,
        leccion__modulo__tipo_empresa=tipo_empresa
    ).select_related('leccion').order_by('-creado_en')
    
    serializer = ProgresoUsuarioSerializer(progreso, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recomendaciones(request):
    """Obtiene recomendaciones personalizadas para el usuario"""
    limite = int(request.GET.get('limite', 3))
    
    recomendaciones = RecommendationService.obtener_recomendaciones_personalizadas(
        request.user, limite=limite
    )
    
    serializer = RecomendacionSerializer(recomendaciones, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def escenarios_list(request):
    """Lista escenarios disponibles por tipo de simulación"""
    tipo_simulacion_id = request.GET.get('tipo_simulacion_id')
    
    queryset = EscenarioSimulacion.objects.filter(activo=True)
    
    if tipo_simulacion_id:
        queryset = queryset.filter(tipo_simulacion_id=tipo_simulacion_id)
    
    escenarios = queryset.select_related('tipo_simulacion').order_by('dificultad', 'nombre')
    serializer = EscenarioSimulacionSerializer(escenarios, many=True)
    return Response(serializer.data)