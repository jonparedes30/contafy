from django.db.models import Q, Avg
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, ProgresoUsuario, PerfilAprendizaje

class RecommendationService:
    
    @staticmethod
    def obtener_siguiente_leccion(usuario):
        """Obtiene la siguiente lección recomendada para el usuario"""
        
        # Obtener perfil del usuario
        perfil, _ = PerfilAprendizaje.objects.get_or_create(usuario=usuario)
        
        # Determinar tipo de empresa del usuario
        tipo_empresa = 'comercial'  # Default
        if hasattr(usuario, 'empresa_set') and usuario.empresa_set.exists():
            tipo_empresa = usuario.empresa_set.first().categoria
        
        # Obtener progreso del usuario
        lecciones_completadas = ProgresoUsuario.objects.filter(
            usuario=usuario,
            completada=True
        ).values_list('leccion_id', flat=True)
        
        # Buscar siguiente lección no completada
        siguiente_leccion = Leccion.objects.filter(
            modulo__tipo_empresa=tipo_empresa,
            visible=True,
            activa=True
        ).exclude(
            id__in=lecciones_completadas
        ).order_by('modulo__orden', 'orden').first()
        
        if not siguiente_leccion:
            # Si no hay más lecciones, sugerir repaso
            return RecommendationService._obtener_leccion_repaso(usuario, tipo_empresa)
        
        return {
            'leccion': siguiente_leccion,
            'tipo': 'siguiente',
            'razon': 'Continúa tu ruta de aprendizaje',
            'dificultad': siguiente_leccion.dificultad,
            'xp_estimado': siguiente_leccion.puntos_xp
        }
    
    @staticmethod
    def obtener_recomendaciones_personalizadas(usuario, limite=3):
        """Obtiene múltiples recomendaciones personalizadas"""
        
        perfil, _ = PerfilAprendizaje.objects.get_or_create(usuario=usuario)
        tipo_empresa = 'comercial'
        if hasattr(usuario, 'empresa_set') and usuario.empresa_set.exists():
            tipo_empresa = usuario.empresa_set.first().categoria
        
        recomendaciones = []
        
        # 1. Siguiente lección en la ruta
        siguiente = RecommendationService.obtener_siguiente_leccion(usuario)
        if siguiente:
            recomendaciones.append(siguiente)
        
        # 2. Lección de repaso si el rendimiento es bajo
        rendimiento_promedio = RecommendationService._calcular_rendimiento_promedio(usuario)
        if rendimiento_promedio < 70:
            repaso = RecommendationService._obtener_leccion_repaso(usuario, tipo_empresa)
            if repaso:
                recomendaciones.append({
                    'leccion': repaso,
                    'tipo': 'repaso',
                    'razon': 'Refuerza conceptos anteriores',
                    'dificultad': repaso.dificultad,
                    'xp_estimado': repaso.puntos_xp // 2
                })
        
        # 3. Lección de desafío si el rendimiento es alto
        if rendimiento_promedio > 85 and perfil.nivel > 1:
            desafio = RecommendationService._obtener_leccion_desafio(usuario, tipo_empresa)
            if desafio:
                recomendaciones.append({
                    'leccion': desafio,
                    'tipo': 'desafio',
                    'razon': 'Pon a prueba tus conocimientos',
                    'dificultad': desafio.dificultad,
                    'xp_estimado': desafio.puntos_xp * 2
                })
        
        return recomendaciones[:limite]
    
    @staticmethod
    def _calcular_rendimiento_promedio(usuario):
        """Calcula el rendimiento promedio del usuario"""
        progreso = ProgresoUsuario.objects.filter(usuario=usuario, completada=True)
        if not progreso.exists():
            return 0
        
        promedio = progreso.aggregate(Avg('puntuacion'))['puntuacion__avg']
        return promedio or 0
    
    @staticmethod
    def _obtener_leccion_repaso(usuario, tipo_empresa):
        """Obtiene una lección para repaso basada en bajo rendimiento"""
        
        # Buscar lecciones completadas con puntuación baja
        progreso_bajo = ProgresoUsuario.objects.filter(
            usuario=usuario,
            completada=True,
            puntuacion__lt=70
        ).order_by('-creado_en')[:5]
        
        if progreso_bajo.exists():
            return progreso_bajo.first().leccion
        
        # Si no hay progreso bajo, devolver una lección básica
        return Leccion.objects.filter(
            modulo__tipo_empresa=tipo_empresa,
            dificultad=1,
            visible=True,
            activa=True
        ).order_by('modulo__orden', 'orden').first()
    
    @staticmethod
    def _obtener_leccion_desafio(usuario, tipo_empresa):
        """Obtiene una lección de desafío para usuarios avanzados"""
        
        lecciones_completadas = ProgresoUsuario.objects.filter(
            usuario=usuario,
            completada=True
        ).values_list('leccion_id', flat=True)
        
        return Leccion.objects.filter(
            modulo__tipo_empresa=tipo_empresa,
            dificultad=3,  # Difícil
            visible=True,
            activa=True
        ).exclude(
            id__in=lecciones_completadas
        ).order_by('?').first()  # Random para variedad
    
    @staticmethod
    def actualizar_recomendaciones_post_leccion(usuario, leccion, puntuacion):
        """Actualiza recomendaciones después de completar una lección"""
        
        perfil, _ = PerfilAprendizaje.objects.get_or_create(usuario=usuario)
        
        # Actualizar nivel si es necesario
        if perfil.xp_total >= perfil.xp_para_siguiente_nivel:
            perfil.nivel += 1
            perfil.save()
        
        # Determinar siguiente acción basada en puntuación
        if puntuacion < 60:
            return {
                'accion': 'repetir',
                'mensaje': 'Te recomendamos repasar esta lección',
                'siguiente': leccion
            }
        elif puntuacion >= 90:
            return {
                'accion': 'avanzar_rapido',
                'mensaje': '¡Excelente! Puedes intentar un desafío',
                'siguiente': RecommendationService._obtener_leccion_desafio(
                    usuario, 
                    leccion.modulo.tipo_empresa
                )
            }
        else:
            return {
                'accion': 'continuar',
                'mensaje': '¡Bien hecho! Continúa con la siguiente lección',
                'siguiente': RecommendationService.obtener_siguiente_leccion(usuario)
            }