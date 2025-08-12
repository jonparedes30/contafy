from django.db import models
from django.conf import settings

class ModuloAprendizaje(models.Model):
    TIPO_EMPRESA_CHOICES = [
        ('comercial', 'Comercial'),
        ('manufactura', 'Manufactura'), 
        ('servicios', 'Servicios'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo_empresa = models.CharField(max_length=20, choices=TIPO_EMPRESA_CHOICES)
    nivel = models.IntegerField(default=1)  # 1=Básico, 2=Intermedio, 3=Avanzado
    descripcion = models.TextField()
    icono = models.CharField(max_length=50, default='fas fa-book')  # FontAwesome icon
    orden = models.IntegerField(default=1)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['tipo_empresa', 'orden']
        verbose_name = 'Módulo de Aprendizaje'
        verbose_name_plural = 'Módulos de Aprendizaje'
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_empresa_display()})"

class Leccion(models.Model):
    TIPO_LECCION_CHOICES = [
        ('teoria', 'Teoría'),
        ('practica', 'Práctica'),
        ('simulacion', 'Simulación'),
        ('quiz', 'Quiz'),
    ]
    
    modulo = models.ForeignKey(ModuloAprendizaje, on_delete=models.CASCADE, related_name='lecciones')
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_LECCION_CHOICES, default='teoria')
    contenido = models.TextField()  # Contenido de la lección
    puntos_xp = models.IntegerField(default=10)
    tiempo_estimado = models.IntegerField(default=5)  # minutos
    orden = models.IntegerField(default=1)
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['modulo', 'orden']
        verbose_name = 'Lección'
        verbose_name_plural = 'Lecciones'
    
    def __str__(self):
        return f"{self.modulo.nombre} - {self.titulo}"

class ProgresoUsuario(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE)
    completada = models.BooleanField(default=False)
    puntuacion = models.IntegerField(default=0)
    intentos = models.IntegerField(default=0)
    tiempo_completado = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['usuario', 'leccion']
        verbose_name = 'Progreso de Usuario'
        verbose_name_plural = 'Progreso de Usuarios'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.leccion.titulo}"

class PerfilAprendizaje(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil_aprendizaje')
    nivel = models.IntegerField(default=1)
    xp_total = models.IntegerField(default=0)
    racha_dias = models.IntegerField(default=0)
    ultima_actividad = models.DateField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Aprendizaje'
        verbose_name_plural = 'Perfiles de Aprendizaje'
    
    def __str__(self):
        return f"{self.usuario.username} - Nivel {self.nivel}"
    
    @property
    def xp_para_siguiente_nivel(self):
        return self.nivel * 100  # 100 XP por nivel
    
    @property
    def xp_porcentaje(self):
        xp_actual = self.xp_total % 100
        return (xp_actual / 100) * 100