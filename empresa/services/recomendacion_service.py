from django.db.models import Avg, Count, Q
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, ProgresoUsuario, PerfilAprendizaje
from empresa.models_simulaciones import SimulacionUsuario
from datetime import datetime, timedelta
import random

class RecomendacionService:
    
    @staticmethod
    def obtener_siguiente_leccion(usuario):
        """Recomienda la siguiente lección basada en progreso y rendimiento"""
        
        # Obtener perfil del usuario
        perfil, _ = PerfilAprendizaje.objects.get_or_create(usuario=usuario)
        tipo_empresa = usuario.empresa.categoria if usuario.empresa else 'comercial'
        
        # Obtener lecciones no completadas del tipo de empresa
        lecciones_disponibles = Leccion.objects.filter(
            modulo__tipo_empresa=tipo_empresa,
            modulo__activo=True,
            activa=True
        ).exclude(
            progresousuario__usuario=usuario,
            progresousuario__completada=True
        ).order_by('modulo__orden', 'orden')
        
        if not lecciones_disponibles.exists():
            return None
            
        # Análisis de rendimiento del usuario
        rendimiento = RecomendacionService._analizar_rendimiento(usuario)
        
        # Seleccionar lección basada en rendimiento
        if rendimiento['promedio_puntuacion'] < 60:
            # Usuario con dificultades - recomendar repaso
            return RecomendacionService._recomendar_repaso(usuario, tipo_empresa)
        elif rendimiento['promedio_puntuacion'] > 85:
            # Usuario avanzado - recomendar desafío
            return RecomendacionService._recomendar_desafio(usuario, lecciones_disponibles)
        else:
            # Usuario promedio - siguiente lección normal
            return lecciones_disponibles.first()
    
    @staticmethod
    def _analizar_rendimiento(usuario):
        """Analiza el rendimiento histórico del usuario"""
        progresos = ProgresoUsuario.objects.filter(
            usuario=usuario,
            completada=True
        ).aggregate(
            promedio_puntuacion=Avg('puntuacion'),
            total_lecciones=Count('id'),
            promedio_intentos=Avg('intentos')
        )
        
        # Análisis de simulaciones
        simulaciones = SimulacionUsuario.objects.filter(
            usuario=usuario,
            estado='completada'
        ).aggregate(
            promedio_sim_puntuacion=Avg('puntuacion_obtenida'),
            total_simulaciones=Count('id')
        )
        
        return {
            'promedio_puntuacion': progresos['promedio_puntuacion'] or 0,
            'total_lecciones': progresos['total_lecciones'] or 0,
            'promedio_intentos': progresos['promedio_intentos'] or 1,
            'promedio_sim_puntuacion': simulaciones['promedio_sim_puntuacion'] or 0,
            'total_simulaciones': simulaciones['total_simulaciones'] or 0
        }
    
    @staticmethod
    def _recomendar_repaso(usuario, tipo_empresa):
        """Recomienda lecciones de repaso para usuarios con dificultades"""
        
        # Buscar lecciones completadas con baja puntuación
        lecciones_debiles = ProgresoUsuario.objects.filter(
            usuario=usuario,
            completada=True,
            puntuacion__lt=70
        ).select_related('leccion').order_by('puntuacion')[:3]
        
        if lecciones_debiles:
            return lecciones_debiles.first().leccion
        
        # Si no hay lecciones débiles, recomendar la primera disponible
        return Leccion.objects.filter(
            modulo__tipo_empresa=tipo_empresa,
            modulo__activo=True,
            activa=True
        ).exclude(
            progresousuario__usuario=usuario,
            progresousuario__completada=True
        ).first()
    
    @staticmethod
    def _recomendar_desafio(usuario, lecciones_disponibles):
        """Recomienda lecciones desafiantes para usuarios avanzados"""
        
        # Priorizar lecciones de simulación o quiz
        lecciones_desafio = lecciones_disponibles.filter(
            tipo__in=['simulacion', 'quiz']
        )
        
        if lecciones_desafio.exists():
            return lecciones_desafio.first()
        
        # Si no hay desafíos, siguiente lección normal
        return lecciones_disponibles.first()
    
    @staticmethod
    def obtener_recomendaciones_dashboard(usuario):
        """Obtiene recomendaciones para mostrar en el dashboard"""
        
        rendimiento = RecomendacionService._analizar_rendimiento(usuario)
        siguiente_leccion = RecomendacionService.obtener_siguiente_leccion(usuario)
        
        # Generar mensaje personalizado
        mensaje = RecomendacionService._generar_mensaje_motivacional(rendimiento)
        
        # Obtener estadísticas de progreso
        tipo_empresa = usuario.empresa.categoria if usuario.empresa else 'comercial'
        total_lecciones = Leccion.objects.filter(
            modulo__tipo_empresa=tipo_empresa,
            modulo__activo=True,
            activa=True
        ).count()
        
        completadas = ProgresoUsuario.objects.filter(
            usuario=usuario,
            completada=True
        ).count()
        
        return {
            'siguiente_leccion': siguiente_leccion,
            'mensaje_motivacional': mensaje,
            'progreso_global': {
                'completadas': completadas,
                'total': total_lecciones,
                'porcentaje': round((completadas / total_lecciones * 100) if total_lecciones > 0 else 0, 1)
            },
            'rendimiento': rendimiento,
            'sugerencias': RecomendacionService._generar_sugerencias(rendimiento)
        }
    
    @staticmethod
    def _generar_mensaje_motivacional(rendimiento):
        """Genera mensaje motivacional basado en rendimiento"""
        
        puntuacion = rendimiento['promedio_puntuacion']
        total_lecciones = rendimiento['total_lecciones']
        
        if total_lecciones == 0:
            return "¡Bienvenido a Academia CONTAFY! Comienza tu primera lección."
        elif puntuacion >= 90:
            return "¡Excelente trabajo! Eres un experto en contabilidad."
        elif puntuacion >= 75:
            return "¡Muy bien! Sigues progresando constantemente."
        elif puntuacion >= 60:
            return "Buen progreso. Sigue practicando para mejorar."
        else:
            return "No te desanimes. Repasa los conceptos básicos."
    
    @staticmethod
    def _generar_sugerencias(rendimiento):
        """Genera sugerencias específicas basadas en rendimiento"""
        
        sugerencias = []
        
        if rendimiento['promedio_puntuacion'] < 70:
            sugerencias.append({
                'tipo': 'repaso',
                'titulo': 'Refuerza conceptos básicos',
                'descripcion': 'Repasa las lecciones anteriores para fortalecer tu base.',
                'icono': 'fas fa-redo'
            })
        
        if rendimiento['promedio_intentos'] > 2:
            sugerencias.append({
                'tipo': 'practica',
                'titulo': 'Más práctica',
                'descripcion': 'Dedica más tiempo a las simulaciones prácticas.',
                'icono': 'fas fa-dumbbell'
            })
        
        if rendimiento['total_simulaciones'] < 3:
            sugerencias.append({
                'tipo': 'simulacion',
                'titulo': 'Prueba simulaciones',
                'descripcion': 'Las simulaciones te ayudan a aplicar lo aprendido.',
                'icono': 'fas fa-play-circle'
            })
        
        # Sugerencia por defecto si no hay problemas específicos
        if not sugerencias:
            sugerencias.append({
                'tipo': 'continuar',
                'titulo': '¡Sigue así!',
                'descripcion': 'Continúa con la siguiente lección para seguir aprendiendo.',
                'icono': 'fas fa-arrow-right'
            })
        
        return sugerencias
    
    @staticmethod
    def registrar_interaccion(usuario, tipo_interaccion, datos=None):
        """Registra interacciones del usuario para mejorar recomendaciones"""
        
        # Por ahora solo actualizar última actividad
        # En el futuro se puede expandir para ML más sofisticado
        perfil, _ = PerfilAprendizaje.objects.get_or_create(usuario=usuario)
        perfil.ultima_actividad = datetime.now().date()
        perfil.save()
        
        return True