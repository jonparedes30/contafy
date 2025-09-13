from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
try:
    # Django 3.1+ provides models.JSONField
    JSONField = models.JSONField
except AttributeError:
    try:
        # Older Django with postgres
        from django.contrib.postgres.fields import JSONField
    except Exception:
        JSONField = None

class ModuloAprendizaje(models.Model):
    TIPO_EMPRESA_CHOICES = [
        ('comercial', 'Comercial'),
        ('manufactura', 'Manufactura'), 
        ('servicios', 'Servicios'),
    ]
    
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    tipo_empresa = models.CharField(max_length=20, choices=TIPO_EMPRESA_CHOICES, db_index=True)
    nivel = models.IntegerField(default=1)  # 1=Básico, 2=Intermedio, 3=Avanzado
    descripcion = models.TextField()
    icono = models.CharField(max_length=50, default='fas fa-book')  # FontAwesome icon
    orden = models.IntegerField(default=1, db_index=True)
    visible = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['tipo_empresa', 'orden']
        verbose_name = 'Módulo de Aprendizaje'
        verbose_name_plural = 'Módulos de Aprendizaje'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
    
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
    slug = models.SlugField(max_length=220)
    tipo = models.CharField(max_length=20, choices=TIPO_LECCION_CHOICES, default='teoria')
    contenido = models.TextField()  # Contenido de la lección
    # Pasos opcionales para lecciones interactivas (micro-lecciones)
    # Estructura esperada: [{"titulo":..., "descripcion":..., "accion":..., "datos": {...}}, ...]
    if JSONField:
        pasos = JSONField(null=True, blank=True)
    else:
        pasos = models.TextField(null=True, blank=True, help_text='JSON con pasos si JSONField no disponible')
    puntos_xp = models.IntegerField(default=10)
    tiempo_estimado = models.IntegerField(default=5)  # minutos
    dificultad = models.IntegerField(default=1, choices=[(1, 'Fácil'), (2, 'Medio'), (3, 'Difícil')])
    orden = models.IntegerField(default=1, db_index=True)
    visible = models.BooleanField(default=True)
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['modulo', 'orden']
        unique_together = [['slug', 'modulo']]
        indexes = [
            models.Index(fields=['modulo', 'orden']),
            models.Index(fields=['tipo', 'visible']),
        ]
        verbose_name = 'Lección'
        verbose_name_plural = 'Lecciones'
    
    def clean(self):
        import json
        if self.pasos:
            try:
                if isinstance(self.pasos, str):
                    pasos_data = json.loads(self.pasos)
                else:
                    pasos_data = self.pasos
                
                if not isinstance(pasos_data, list):
                    raise ValidationError('Los pasos deben ser una lista')
                
                for i, paso in enumerate(pasos_data):
                    if not isinstance(paso, dict):
                        raise ValidationError(f'Paso {i+1} debe ser un objeto')
                    if 'titulo' not in paso:
                        raise ValidationError(f'Paso {i+1} debe tener titulo')
                        
            except json.JSONDecodeError:
                raise ValidationError('JSON de pasos inválido')
        
        from django.core.exceptions import ValidationError
        super().clean()
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)
    
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


class PasoCompletado(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE)
    paso_index = models.IntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'leccion', 'paso_index')
        verbose_name = 'Paso Completado'
        verbose_name_plural = 'Pasos Completados'

    def __str__(self):
        return f"{self.usuario.username} - {self.leccion.titulo} - paso {self.paso_index}"