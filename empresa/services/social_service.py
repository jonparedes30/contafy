from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime
from empresa.models_social import Liga, ParticipanteLiga, Reto, LogroCompartido
from empresa.models_gamificacion import PerfilAprendizaje, LogroUsuario

class SocialService:
    """Servicio para funcionalidades sociales de la academia"""
    
    @staticmethod
    def crear_liga_semanal():
        """Crea una nueva liga semanal automáticamente"""
        ahora = timezone.now()
        inicio_semana = ahora - timedelta(days=ahora.weekday())
        fin_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59)
        
        liga, created = Liga.objects.get_or_create(
            fecha_inicio__date=inicio_semana.date(),
            defaults={
                'nombre': f'Liga Semanal {inicio_semana.strftime("%d/%m")}',
                'fecha_inicio': inicio_semana,
                'fecha_fin': fin_semana,
                'activa': True
            }
        )
        
        if created:
            # Inscribir automáticamente a usuarios activos
            usuarios_activos = User.objects.filter(
                is_active=True,
                perfilaprendizaje__isnull=False
            )
            
            for usuario in usuarios_activos:
                perfil = PerfilAprendizaje.objects.get(usuario=usuario)
                ParticipanteLiga.objects.create(
                    liga=liga,
                    usuario=usuario,
                    xp_inicial=perfil.xp_total
                )
        
        return liga
    
    @staticmethod
    def actualizar_posiciones_liga(liga):
        """Actualiza las posiciones en una liga"""
        participantes = ParticipanteLiga.objects.filter(liga=liga).select_related('usuario__perfilaprendizaje')
        
        # Calcular XP ganada durante la liga
        for participante in participantes:
            perfil_actual = PerfilAprendizaje.objects.get(usuario=participante.usuario)
            participante.xp_ganada = max(0, perfil_actual.xp_total - participante.xp_inicial)
            participante.save()
        
        # Ordenar por XP ganada y asignar posiciones
        participantes_ordenados = participantes.order_by('-xp_ganada')
        for i, participante in enumerate(participantes_ordenados, 1):
            participante.posicion = i
            participante.save()
    
    @staticmethod
    def obtener_tabla_clasificacion(liga=None, limite=10):
        """Obtiene la tabla de clasificación actual"""
        if not liga:
            liga = Liga.objects.filter(activa=True).first()
        
        if not liga:
            return []
        
        SocialService.actualizar_posiciones_liga(liga)
        
        return ParticipanteLiga.objects.filter(liga=liga).select_related(
            'usuario', 'usuario__perfilaprendizaje'
        ).order_by('posicion')[:limite]
    
    @staticmethod
    def crear_reto(creador, retado, tipo, objetivo, dias_limite=7):
        """Crea un reto entre dos usuarios"""
        fecha_limite = timezone.now() + timedelta(days=dias_limite)
        
        reto = Reto.objects.create(
            creador=creador,
            retado=retado,
            tipo=tipo,
            objetivo=objetivo,
            fecha_limite=fecha_limite
        )
        
        return reto
    
    @staticmethod
    def verificar_retos_usuario(usuario):
        """Verifica el progreso de los retos activos de un usuario"""
        retos_activos = Reto.objects.filter(
            models.Q(creador=usuario) | models.Q(retado=usuario),
            activo=True,
            fecha_limite__gt=timezone.now()
        )
        
        for reto in retos_activos:
            # Verificar progreso del creador
            if not reto.completado_creador:
                progreso_creador = SocialService._obtener_progreso_reto(reto.creador, reto)
                if progreso_creador >= reto.objetivo:
                    reto.completado_creador = True
            
            # Verificar progreso del retado
            if not reto.completado_retado:
                progreso_retado = SocialService._obtener_progreso_reto(reto.retado, reto)
                if progreso_retado >= reto.objetivo:
                    reto.completado_retado = True
            
            # Determinar ganador si ambos completaron o se acabó el tiempo
            if (reto.completado_creador and reto.completado_retado) or timezone.now() > reto.fecha_limite:
                if reto.completado_creador and not reto.completado_retado:
                    reto.ganador = reto.creador
                elif reto.completado_retado and not reto.completado_creador:
                    reto.ganador = reto.retado
                elif reto.completado_creador and reto.completado_retado:
                    # Empate - el que completó primero gana (simplificado)
                    reto.ganador = reto.creador
                
                reto.activo = False
            
            reto.save()
        
        return retos_activos
    
    @staticmethod
    def _obtener_progreso_reto(usuario, reto):
        """Obtiene el progreso actual de un usuario en un reto específico"""
        from empresa.models_aprendizaje import ProgresoUsuario
        from empresa.models_simulaciones import SimulacionUsuario
        
        if reto.tipo == 'lecciones':
            return ProgresoUsuario.objects.filter(
                usuario=usuario,
                completada=True,
                tiempo_completado__gte=reto.fecha_inicio if hasattr(reto, 'fecha_inicio') else timezone.now() - timedelta(days=7)
            ).count()
        
        elif reto.tipo == 'xp':
            perfil = PerfilAprendizaje.objects.get(usuario=usuario)
            # Simplificado: usar XP total actual
            return perfil.xp_total
        
        elif reto.tipo == 'simulaciones':
            return SimulacionUsuario.objects.filter(
                usuario=usuario,
                completada=True,
                fecha_completado__gte=reto.fecha_inicio if hasattr(reto, 'fecha_inicio') else timezone.now() - timedelta(days=7)
            ).count()
        
        return 0
    
    @staticmethod
    def compartir_logro(usuario, logro_usuario, mensaje=""):
        """Permite a un usuario compartir un logro"""
        logro_compartido = LogroCompartido.objects.create(
            usuario=usuario,
            logro_usuario=logro_usuario,
            mensaje=mensaje
        )
        
        return logro_compartido
    
    @staticmethod
    def obtener_feed_social(usuario, limite=20):
        """Obtiene el feed social de logros compartidos"""
        # Por ahora, mostrar todos los logros compartidos
        # En el futuro se puede filtrar por amigos/compañeros de empresa
        return LogroCompartido.objects.select_related(
            'usuario', 'logro_usuario__logro'
        ).prefetch_related('likes')[:limite]
    
    @staticmethod
    def dar_like_logro(usuario, logro_compartido):
        """Permite dar like a un logro compartido"""
        logro_compartido.likes.add(usuario)
        return True
    
    @staticmethod
    def quitar_like_logro(usuario, logro_compartido):
        """Permite quitar like a un logro compartido"""
        logro_compartido.likes.remove(usuario)
        return True