from django.utils import timezone
from datetime import date, timedelta
from empresa.models_aprendizaje import PerfilAprendizaje, ProgresoUsuario
from empresa.models_gamificacion import Logro, LogroUsuario, ActividadDiaria, Insignia, InsigniaUsuario

class GamificacionService:
    
    @staticmethod
    def otorgar_xp(usuario, puntos_xp, concepto="Actividad completada"):
        """Otorga XP al usuario y actualiza su nivel"""
        perfil, created = PerfilAprendizaje.objects.get_or_create(usuario=usuario)
        
        # Guardar XP anterior para calcular si subió de nivel
        xp_anterior = perfil.xp_total
        nivel_anterior = perfil.nivel
        
        # Otorgar XP
        perfil.xp_total += puntos_xp
        
        # Calcular nuevo nivel (cada 100 XP = 1 nivel)
        nuevo_nivel = (perfil.xp_total // 100) + 1
        subio_nivel = nuevo_nivel > nivel_anterior
        
        if subio_nivel:
            perfil.nivel = nuevo_nivel
        
        perfil.save()
        
        # Registrar actividad diaria
        GamificacionService.registrar_actividad_diaria(usuario, xp_ganada=puntos_xp)
        
        # Verificar logros
        GamificacionService.verificar_logros(usuario)
        
        return {
            'xp_otorgada': puntos_xp,
            'xp_total': perfil.xp_total,
            'nivel_anterior': nivel_anterior,
            'nivel_actual': perfil.nivel,
            'subio_nivel': subio_nivel
        }
    
    @staticmethod
    def registrar_actividad_diaria(usuario, lecciones=0, xp_ganada=0, tiempo_minutos=0):
        """Registra la actividad diaria del usuario"""
        hoy = date.today()
        actividad, created = ActividadDiaria.objects.get_or_create(
            usuario=usuario,
            fecha=hoy,
            defaults={
                'lecciones_completadas': lecciones,
                'xp_ganada': xp_ganada,
                'tiempo_estudiado': tiempo_minutos
            }
        )
        
        if not created:
            actividad.lecciones_completadas += lecciones
            actividad.xp_ganada += xp_ganada
            actividad.tiempo_estudiado += tiempo_minutos
            actividad.save()
        
        # Actualizar racha de días
        GamificacionService.actualizar_racha(usuario)
        
        return actividad
    
    @staticmethod
    def actualizar_racha(usuario):
        """Actualiza la racha de días consecutivos del usuario"""
        perfil, created = PerfilAprendizaje.objects.get_or_create(usuario=usuario)
        
        # Obtener actividades de los últimos días
        hoy = date.today()
        ayer = hoy - timedelta(days=1)
        
        # Verificar si hay actividad hoy
        actividad_hoy = ActividadDiaria.objects.filter(
            usuario=usuario,
            fecha=hoy,
            lecciones_completadas__gt=0
        ).exists()
        
        if actividad_hoy:
            # Verificar si hay actividad ayer para continuar racha
            actividad_ayer = ActividadDiaria.objects.filter(
                usuario=usuario,
                fecha=ayer,
                lecciones_completadas__gt=0
            ).exists()
            
            if actividad_ayer or perfil.racha_dias == 0:
                perfil.racha_dias += 1
            else:
                perfil.racha_dias = 1
        else:
            # Si no hay actividad hoy, verificar si se rompió la racha
            if perfil.ultima_actividad < hoy - timedelta(days=1):
                perfil.racha_dias = 0
        
        perfil.save()
        return perfil.racha_dias
    
    @staticmethod
    def verificar_logros(usuario):
        """Verifica y otorga logros al usuario"""
        perfil = PerfilAprendizaje.objects.get(usuario=usuario)
        logros_otorgados = []
        
        # Obtener logros que el usuario no tiene
        logros_disponibles = Logro.objects.filter(activo=True).exclude(
            id__in=LogroUsuario.objects.filter(usuario=usuario).values_list('logro_id', flat=True)
        )
        
        for logro in logros_disponibles:
            cumple_condicion = False
            
            if logro.tipo == 'puntos_xp':
                cumple_condicion = perfil.xp_total >= logro.condicion_valor
            
            elif logro.tipo == 'racha_dias':
                cumple_condicion = perfil.racha_dias >= logro.condicion_valor
            
            elif logro.tipo == 'completar_modulo':
                # Contar módulos completados
                from empresa.models_aprendizaje import ModuloAprendizaje
                modulos_completados = 0
                modulos = ModuloAprendizaje.objects.filter(
                    tipo_empresa=usuario.empresa.categoria if usuario.empresa else 'comercial'
                )
                
                for modulo in modulos:
                    total_lecciones = modulo.lecciones.filter(activa=True).count()
                    lecciones_completadas = ProgresoUsuario.objects.filter(
                        usuario=usuario,
                        leccion__modulo=modulo,
                        completada=True
                    ).count()
                    
                    if total_lecciones > 0 and lecciones_completadas == total_lecciones:
                        modulos_completados += 1
                
                cumple_condicion = modulos_completados >= logro.condicion_valor
            
            if cumple_condicion:
                # Otorgar logro
                logro_usuario = LogroUsuario.objects.create(
                    usuario=usuario,
                    logro=logro
                )
                
                # Otorgar XP del premio
                if logro.puntos_xp_premio > 0:
                    GamificacionService.otorgar_xp(usuario, logro.puntos_xp_premio, f"Logro: {logro.nombre}")
                
                logros_otorgados.append(logro_usuario)
        
        return logros_otorgados
    
    @staticmethod
    def obtener_estadisticas_usuario(usuario):
        """Obtiene estadísticas completas del usuario"""
        perfil, created = PerfilAprendizaje.objects.get_or_create(usuario=usuario)
        
        # Logros obtenidos
        logros = LogroUsuario.objects.filter(usuario=usuario).select_related('logro')
        
        # Insignias obtenidas
        insignias = InsigniaUsuario.objects.filter(usuario=usuario).select_related('insignia')
        
        # Actividad de la última semana
        hace_semana = date.today() - timedelta(days=7)
        actividad_semanal = ActividadDiaria.objects.filter(
            usuario=usuario,
            fecha__gte=hace_semana
        ).order_by('fecha')
        
        # Progreso total
        lecciones_completadas = ProgresoUsuario.objects.filter(
            usuario=usuario,
            completada=True
        ).count()
        
        return {
            'perfil': perfil,
            'logros': logros,
            'insignias': insignias,
            'actividad_semanal': actividad_semanal,
            'lecciones_completadas': lecciones_completadas,
            'xp_para_siguiente_nivel': 100 - (perfil.xp_total % 100),
            'progreso_nivel': (perfil.xp_total % 100)
        }
    
    @staticmethod
    def obtener_ranking_semanal(tipo_empresa=None, limite=10):
        """Obtiene el ranking semanal de usuarios"""
        from datetime import datetime, timedelta
        from django.db.models import Sum
        
        hoy = datetime.now().date()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        
        query = ActividadDiaria.objects.filter(fecha__gte=inicio_semana)
        
        if tipo_empresa:
            query = query.filter(usuario__empresa__categoria=tipo_empresa)
        
        ranking = query.values(
            'usuario__username',
            'usuario__id'
        ).annotate(
            xp_semanal=Sum('xp_ganada'),
            lecciones_semanal=Sum('lecciones_completadas')
        ).order_by('-xp_semanal')[:limite]
        
        return list(ranking)
    
    @staticmethod
    def crear_liga_semanal():
        """Crea una nueva liga semanal"""
        from datetime import datetime, timedelta
        from empresa.models_gamificacion import Liga
        
        hoy = datetime.now()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59)
        
        liga, created = Liga.objects.get_or_create(
            tipo='semanal',
            fecha_inicio__date=inicio_semana.date(),
            defaults={
                'nombre': f'Liga Semanal {inicio_semana.strftime("%d/%m")}',
                'fecha_inicio': inicio_semana,
                'fecha_fin': fin_semana,
                'premio_xp': 200
            }
        )
        
        return liga
    
    @staticmethod
    def actualizar_puntos_liga(usuario, puntos):
        """Actualiza los puntos del usuario en la liga activa"""
        from empresa.models_gamificacion import Liga, ParticipacionLiga
        from datetime import datetime
        
        liga_activa = Liga.objects.filter(
            activa=True,
            fecha_inicio__lte=datetime.now(),
            fecha_fin__gte=datetime.now()
        ).first()
        
        if liga_activa:
            participacion, created = ParticipacionLiga.objects.get_or_create(
                usuario=usuario,
                liga=liga_activa
            )
            
            participacion.puntos_obtenidos += puntos
            participacion.save()
            
            return participacion
        
        return None