from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class LigaSemanal(models.Model):
    """Ligas semanales para competencia entre usuarios"""
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.nombre} ({self.fecha_inicio.strftime('%Y-%m-%d')})"

class ParticipanteLiga(models.Model):
    """Participación de usuarios en ligas"""
    liga = models.ForeignKey(LigaSemanal, on_delete=models.CASCADE, related_name='participantes')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    xp_inicial = models.IntegerField(default=0)
    xp_ganada = models.IntegerField(default=0)
    posicion = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ['liga', 'usuario']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.liga.nombre}"

class RetoSocial(models.Model):
    """Retos entre empleados"""
    TIPOS = [
        ('lecciones', 'Completar Lecciones'),
        ('xp', 'Ganar XP'),
        ('simulaciones', 'Completar Simulaciones'),
    ]
    
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retos_creados')
    retado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retos_recibidos')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    objetivo = models.IntegerField()  # Meta a alcanzar
    fecha_limite = models.DateTimeField()
    completado_creador = models.BooleanField(default=False)
    completado_retado = models.BooleanField(default=False)
    ganador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Reto {self.tipo}: {self.creador.username} vs {self.retado.username}"

class LogroCompartido(models.Model):
    """Logros compartidos por usuarios"""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    logro_usuario = models.ForeignKey('empresa.LogroUsuario', on_delete=models.CASCADE)
    mensaje = models.TextField(blank=True)
    fecha_compartido = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='likes_logros', blank=True)
    
    class Meta:
        ordering = ['-fecha_compartido']
    
    def __str__(self):
        return f"{self.usuario.username} compartió: {self.logro_usuario.logro.nombre}"