from django.db import models
from django.conf import settings
import json

class TipoSimulacion(models.Model):
    CATEGORIA_CHOICES = [
        ('comercial', 'Comercial'),
        ('manufactura', 'Manufactura'),
        ('servicios', 'Servicios'),
    ]
    
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    descripcion = models.TextField()
    icono = models.CharField(max_length=50, default='fas fa-play-circle')
    configuracion = models.JSONField(default=dict, help_text="Configuración específica de la simulación")
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Tipo de Simulación'
        verbose_name_plural = 'Tipos de Simulaciones'
    
    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"

class SimulacionUsuario(models.Model):
    ESTADO_CHOICES = [
        ('iniciada', 'Iniciada'),
        ('completada', 'Completada'),
        ('fallida', 'Fallida'),
    ]
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='simulaciones')
    tipo_simulacion = models.ForeignKey(TipoSimulacion, on_delete=models.CASCADE)
    leccion = models.ForeignKey('empresa.Leccion', on_delete=models.CASCADE, null=True, blank=True)
    escenario = models.ForeignKey('EscenarioSimulacion', on_delete=models.CASCADE, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='iniciada')
    datos_entrada = models.JSONField(default=dict, help_text="Datos ingresados por el usuario")
    resultado = models.JSONField(default=dict, help_text="Resultado de la simulación")
    puntuacion = models.IntegerField(default=0)
    tiempo_completado = models.IntegerField(default=0, help_text="Tiempo en segundos")
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    es_sandbox = models.BooleanField(default=False, help_text="Indica si la simulación se ejecutó en modo sandbox")
    
    class Meta:
        verbose_name = 'Simulación de Usuario'
        verbose_name_plural = 'Simulaciones de Usuarios'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.tipo_simulacion.nombre}"

class EscenarioSimulacion(models.Model):
    """Escenarios predefinidos para simulaciones"""
    tipo_simulacion = models.ForeignKey(TipoSimulacion, on_delete=models.CASCADE, related_name='escenarios')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    datos_iniciales = models.JSONField(default=dict, help_text="Datos iniciales del escenario")
    solucion_esperada = models.JSONField(default=dict, help_text="Solución correcta")
    dificultad = models.IntegerField(default=1, choices=[(1, 'Fácil'), (2, 'Medio'), (3, 'Difícil')])
    puntos_max = models.IntegerField(default=100)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Escenario de Simulación'
        verbose_name_plural = 'Escenarios de Simulaciones'
    
    def __str__(self):
        return f"{self.tipo_simulacion.nombre} - {self.nombre}"