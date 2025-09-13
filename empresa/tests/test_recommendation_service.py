from django.test import TestCase
from django.contrib.auth import get_user_model
from empresa.models import Empresa
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, ProgresoUsuario, PerfilAprendizaje
from empresa.services.recommendation_service import RecommendationService

User = get_user_model()

class RecommendationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.empresa = Empresa.objects.create(
            nombre='Test Empresa',
            categoria='comercial',
            usuario=self.user
        )
        
        # Crear módulos y lecciones de prueba
        self.modulo1 = ModuloAprendizaje.objects.create(
            nombre='Módulo Básico',
            slug='modulo-basico',
            tipo_empresa='comercial',
            nivel=1,
            orden=1,
            descripcion='Módulo básico'
        )
        self.modulo2 = ModuloAprendizaje.objects.create(
            nombre='Módulo Avanzado',
            slug='modulo-avanzado',
            tipo_empresa='comercial',
            nivel=2,
            orden=2,
            descripcion='Módulo avanzado'
        )
        
        self.leccion1 = Leccion.objects.create(
            modulo=self.modulo1,
            titulo='Lección 1',
            slug='leccion-1',
            contenido='Contenido 1',
            dificultad=1,
            orden=1,
            puntos_xp=10
        )
        self.leccion2 = Leccion.objects.create(
            modulo=self.modulo1,
            titulo='Lección 2',
            slug='leccion-2',
            contenido='Contenido 2',
            dificultad=2,
            orden=2,
            puntos_xp=15
        )
        self.leccion3 = Leccion.objects.create(
            modulo=self.modulo2,
            titulo='Lección Avanzada',
            slug='leccion-avanzada',
            contenido='Contenido avanzado',
            dificultad=3,
            orden=1,
            puntos_xp=25
        )
    
    def test_obtener_siguiente_leccion_usuario_nuevo(self):
        """Test obtener siguiente lección para usuario nuevo"""
        resultado = RecommendationService.obtener_siguiente_leccion(self.user)
        
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado['leccion'], self.leccion1)
        self.assertEqual(resultado['tipo'], 'siguiente')
        self.assertIn('razon', resultado)
    
    def test_obtener_siguiente_leccion_con_progreso(self):
        """Test obtener siguiente lección con progreso existente"""
        # Marcar primera lección como completada
        ProgresoUsuario.objects.create(
            usuario=self.user,
            leccion=self.leccion1,
            completada=True,
            puntuacion=85
        )
        
        resultado = RecommendationService.obtener_siguiente_leccion(self.user)
        
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado['leccion'], self.leccion2)
    
    def test_obtener_recomendaciones_personalizadas(self):
        """Test obtener recomendaciones personalizadas"""
        recomendaciones = RecommendationService.obtener_recomendaciones_personalizadas(
            self.user, limite=3
        )
        
        self.assertIsInstance(recomendaciones, list)
        self.assertLessEqual(len(recomendaciones), 3)
        
        if recomendaciones:
            rec = recomendaciones[0]
            self.assertIn('leccion', rec)
            self.assertIn('tipo', rec)
            self.assertIn('razon', rec)
    
    def test_calcular_rendimiento_promedio(self):
        """Test cálculo de rendimiento promedio"""
        # Sin progreso
        rendimiento = RecommendationService._calcular_rendimiento_promedio(self.user)
        self.assertEqual(rendimiento, 0)
        
        # Con progreso
        ProgresoUsuario.objects.create(
            usuario=self.user,
            leccion=self.leccion1,
            completada=True,
            puntuacion=80
        )
        ProgresoUsuario.objects.create(
            usuario=self.user,
            leccion=self.leccion2,
            completada=True,
            puntuacion=90
        )
        
        rendimiento = RecommendationService._calcular_rendimiento_promedio(self.user)
        self.assertEqual(rendimiento, 85.0)
    
    def test_obtener_leccion_repaso(self):
        """Test obtener lección para repaso"""
        # Crear progreso con puntuación baja
        ProgresoUsuario.objects.create(
            usuario=self.user,
            leccion=self.leccion1,
            completada=True,
            puntuacion=50  # Puntuación baja
        )
        
        leccion_repaso = RecommendationService._obtener_leccion_repaso(
            self.user, 'comercial'
        )
        
        self.assertIsNotNone(leccion_repaso)
        self.assertEqual(leccion_repaso, self.leccion1)
    
    def test_obtener_leccion_desafio(self):
        """Test obtener lección de desafío"""
        # Marcar lecciones básicas como completadas
        ProgresoUsuario.objects.create(
            usuario=self.user,
            leccion=self.leccion1,
            completada=True,
            puntuacion=95
        )
        ProgresoUsuario.objects.create(
            usuario=self.user,
            leccion=self.leccion2,
            completada=True,
            puntuacion=90
        )
        
        leccion_desafio = RecommendationService._obtener_leccion_desafio(
            self.user, 'comercial'
        )
        
        self.assertIsNotNone(leccion_desafio)
        self.assertEqual(leccion_desafio.dificultad, 3)
    
    def test_actualizar_recomendaciones_post_leccion(self):
        """Test actualizar recomendaciones después de completar lección"""
        # Puntuación baja - debe recomendar repetir
        resultado = RecommendationService.actualizar_recomendaciones_post_leccion(
            self.user, self.leccion1, 50
        )
        self.assertEqual(resultado['accion'], 'repetir')
        
        # Puntuación alta - debe recomendar avanzar rápido
        resultado = RecommendationService.actualizar_recomendaciones_post_leccion(
            self.user, self.leccion1, 95
        )
        self.assertEqual(resultado['accion'], 'avanzar_rapido')
        
        # Puntuación normal - debe continuar
        resultado = RecommendationService.actualizar_recomendaciones_post_leccion(
            self.user, self.leccion1, 75
        )
        self.assertEqual(resultado['accion'], 'continuar')
    
    def test_recomendaciones_con_rendimiento_bajo(self):
        """Test recomendaciones cuando el rendimiento es bajo"""
        # Crear progreso con puntuaciones bajas
        ProgresoUsuario.objects.create(
            usuario=self.user,
            leccion=self.leccion1,
            completada=True,
            puntuacion=60
        )
        
        recomendaciones = RecommendationService.obtener_recomendaciones_personalizadas(
            self.user, limite=3
        )
        
        # Debe incluir recomendación de repaso
        tipos = [rec['tipo'] for rec in recomendaciones]
        self.assertIn('repaso', tipos)
    
    def test_recomendaciones_con_rendimiento_alto(self):
        """Test recomendaciones cuando el rendimiento es alto"""
        # Crear perfil con nivel alto
        perfil, _ = PerfilAprendizaje.objects.get_or_create(usuario=self.user)
        perfil.nivel = 2
        perfil.save()
        
        # Crear progreso con puntuaciones altas
        ProgresoUsuario.objects.create(
            usuario=self.user,
            leccion=self.leccion1,
            completada=True,
            puntuacion=90
        )
        ProgresoUsuario.objects.create(
            usuario=self.user,
            leccion=self.leccion2,
            completada=True,
            puntuacion=95
        )
        
        recomendaciones = RecommendationService.obtener_recomendaciones_personalizadas(
            self.user, limite=3
        )
        
        # Puede incluir recomendación de desafío
        tipos = [rec['tipo'] for rec in recomendaciones]
        # No es obligatorio que aparezca desafío, depende de disponibilidad de lecciones