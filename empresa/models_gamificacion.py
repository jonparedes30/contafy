from django.db import models
from django.conf import settings
from django.utils import timezone

class Logro(models.Model):
    TIPO_CHOICES = [
        ('completar_modulo', 'Completar Módulo'),
        ('racha_dias', 'Racha de Días'),
        ('puntos_xp', 'Puntos XP'),
        ('primera_vez', 'Primera Vez'),
        ('maestria', 'Maestría'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    icono = models.CharField(max_length=50, default='fas fa-trophy')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    condicion_valor = models.IntegerField(help_text="Valor necesario para desbloquear")
    puntos_xp_premio = models.IntegerField(default=50)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Logro'
        verbose_name_plural = 'Logros'
    
    def __str__(self):
        return self.nombre

class LogroUsuario(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='logros_obtenidos')
    logro = models.ForeignKey(Logro, on_delete=models.CASCADE)
    desbloqueado_en = models.DateTimeField(auto_now_add=True)
    notificado = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['usuario', 'logro']
        verbose_name = 'Logro de Usuario'
        verbose_name_plural = 'Logros de Usuarios'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.logro.nombre}"

class ActividadDiaria(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='actividades_diarias')
    fecha = models.DateField()
    lecciones_completadas = models.IntegerField(default=0)
    xp_ganada = models.IntegerField(default=0)
    tiempo_estudiado = models.IntegerField(default=0)  # minutos
    
    class Meta:
        unique_together = ['usuario', 'fecha']
        verbose_name = 'Actividad Diaria'
        verbose_name_plural = 'Actividades Diarias'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.fecha}"

class Insignia(models.Model):
    CATEGORIA_CHOICES = [
        ('comercial', 'Comercial'),
        ('manufactura', 'Manufactura'),
        ('servicios', 'Servicios'),
        ('general', 'General'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    icono = models.CharField(max_length=50, default='fas fa-medal')
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='general')
    color = models.CharField(max_length=7, default='#FFD700', help_text="Color hex de la insignia")
    requisito_xp = models.IntegerField(default=100)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Insignia'
        verbose_name_plural = 'Insignias'
    
    def __str__(self):
        return self.nombre

class InsigniaUsuario(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insignias_obtenidas')
    insignia = models.ForeignKey(Insignia, on_delete=models.CASCADE)
    obtenida_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['usuario', 'insignia']
        verbose_name = 'Insignia de Usuario'
        verbose_name_plural = 'Insignias de Usuarios'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.insignia.nombre}"