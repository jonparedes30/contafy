from rest_framework import serializers
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, ProgresoUsuario
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario, EscenarioSimulacion

class ModuloAprendizajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuloAprendizaje
        fields = ['id', 'nombre', 'slug', 'tipo_empresa', 'nivel', 'descripcion', 'icono', 'orden']

class LeccionSerializer(serializers.ModelSerializer):
    modulo = ModuloAprendizajeSerializer(read_only=True)
    
    class Meta:
        model = Leccion
        fields = ['id', 'titulo', 'slug', 'tipo', 'contenido', 'pasos', 'puntos_xp', 
                 'tiempo_estimado', 'dificultad', 'orden', 'modulo']

class LeccionListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listas"""
    class Meta:
        model = Leccion
        fields = ['id', 'titulo', 'slug', 'tipo', 'puntos_xp', 'tiempo_estimado', 'dificultad']

class TipoSimulacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoSimulacion
        fields = ['id', 'nombre', 'categoria', 'descripcion', 'icono']

class EscenarioSimulacionSerializer(serializers.ModelSerializer):
    tipo_simulacion = TipoSimulacionSerializer(read_only=True)
    
    class Meta:
        model = EscenarioSimulacion
        fields = ['id', 'nombre', 'descripcion', 'datos_iniciales', 'dificultad', 
                 'puntos_max', 'tipo_simulacion']

class SimulacionUsuarioSerializer(serializers.ModelSerializer):
    tipo_simulacion = TipoSimulacionSerializer(read_only=True)
    escenario = EscenarioSimulacionSerializer(read_only=True)
    
    class Meta:
        model = SimulacionUsuario
        fields = ['id', 'estado', 'datos_entrada', 'resultado', 'puntuacion', 
                 'tiempo_completado', 'fecha_inicio', 'fecha_completado', 'es_sandbox',
                 'tipo_simulacion', 'escenario']
        read_only_fields = ['fecha_inicio', 'fecha_completado']

class SimulacionCreateSerializer(serializers.Serializer):
    tipo_simulacion_id = serializers.IntegerField()
    leccion_id = serializers.IntegerField(required=False)
    escenario_id = serializers.IntegerField(required=False)
    modo_sandbox = serializers.BooleanField(default=True)

class SimulacionGuardarSerializer(serializers.Serializer):
    datos_usuario = serializers.JSONField()
    
class ProgresoUsuarioSerializer(serializers.ModelSerializer):
    leccion = LeccionListSerializer(read_only=True)
    
    class Meta:
        model = ProgresoUsuario
        fields = ['id', 'leccion', 'completada', 'puntuacion', 'intentos', 
                 'tiempo_completado', 'creado_en']

class RecomendacionSerializer(serializers.Serializer):
    leccion = LeccionListSerializer()
    tipo = serializers.CharField()
    razon = serializers.CharField()
    dificultad = serializers.IntegerField()
    xp_estimado = serializers.IntegerField()