from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from empresa.models import Empresa
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion, ProgresoUsuario

User = get_user_model()

class FrontendAprendizajeTests(TestCase):
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
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Crear contenido de prueba
        self.modulo = ModuloAprendizaje.objects.create(
            nombre='Módulo Test',
            slug='modulo-test',
            tipo_empresa='comercial',
            descripcion='Test'
        )
        self.leccion = Leccion.objects.create(
            modulo=self.modulo,
            titulo='Lección Test',
            slug='leccion-test',
            contenido='Contenido test',
            pasos=[
                {'titulo': 'Paso 1', 'descripcion': 'Test paso 1', 'accion': 'leer'},
                {'titulo': 'Paso 2', 'descripcion': 'Test paso 2', 'accion': 'quiz', 
                 'datos': {'pregunta': '¿Test?', 'opciones': ['A', 'B'], 'correcta': 0}}
            ],
            puntos_xp=20
        )
    
    def test_aprendizaje_dashboard_view(self):
        """Test vista del dashboard de aprendizaje"""
        response = self.client.get('/aprendizaje/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Módulo Test')
        self.assertContains(response, 'Academia CONTAFY')
    
    def test_leccion_interactiva_view(self):
        """Test vista de lección interactiva"""
        response = self.client.get(f'/aprendizaje/leccion/{self.leccion.id}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lección Test')
        self.assertContains(response, 'Paso 1')
        self.assertContains(response, 'Paso 2')
        self.assertContains(response, 'aprendizaje.css')
        self.assertContains(response, 'aprendizaje.js')
    
    def test_leccion_interactiva_pasos_rendering(self):
        """Test que los pasos se renderizan correctamente"""
        response = self.client.get(f'/aprendizaje/leccion/{self.leccion.id}/')
        
        # Verificar que los pasos están presentes
        self.assertContains(response, 'data-step="0"')
        self.assertContains(response, 'data-step="1"')
        self.assertContains(response, 'Test paso 1')
        self.assertContains(response, '¿Test?')
    
    def test_marcar_leccion_completada(self):
        """Test marcar lección como completada"""
        url = f'/aprendizaje/leccion/{self.leccion.id}/completar/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se creó el progreso
        progreso = ProgresoUsuario.objects.get(
            usuario=self.user,
            leccion=self.leccion
        )
        self.assertTrue(progreso.completada)
        self.assertEqual(progreso.puntuacion, 100)
    
    def test_marcar_paso_completado(self):
        """Test marcar paso específico como completado"""
        url = f'/aprendizaje/leccion/{self.leccion.id}/paso/0/completar/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar respuesta JSON
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('xp_ganado', data)
    
    def test_modulo_detalle_view(self):
        """Test vista de detalle de módulo"""
        response = self.client.get(f'/aprendizaje/modulo/{self.modulo.id}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Módulo Test')
        self.assertContains(response, 'Lección Test')
    
    def test_perfil_aprendizaje_view(self):
        """Test vista del perfil de aprendizaje"""
        response = self.client.get('/aprendizaje/perfil/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Perfil de Aprendizaje')
    
    def test_leccion_requires_login(self):
        """Test que las vistas requieren login"""
        self.client.logout()
        
        response = self.client.get(f'/aprendizaje/leccion/{self.leccion.id}/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_leccion_con_simulacion_rendering(self):
        """Test renderizado de lección con simulación"""
        # Crear lección con simulación
        leccion_sim = Leccion.objects.create(
            modulo=self.modulo,
            titulo='Lección Simulación',
            slug='leccion-simulacion',
            contenido='Test simulación',
            pasos=[
                {
                    'titulo': 'Simulación Venta',
                    'descripcion': 'Practica una venta',
                    'accion': 'simulacion',
                    'datos': {'tipo': 'venta'}
                }
            ]
        )
        
        response = self.client.get(f'/aprendizaje/leccion/{leccion_sim.id}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar Simulación de Venta')
        self.assertContains(response, 'data-action="start-simulation"')
        self.assertContains(response, 'Práctica (Sandbox)')
    
    def test_css_and_js_loading(self):
        """Test que CSS y JS se cargan correctamente"""
        response = self.client.get(f'/aprendizaje/leccion/{self.leccion.id}/')
        
        # Verificar que se incluyen los archivos estáticos
        self.assertContains(response, 'aprendizaje.css')
        self.assertContains(response, 'aprendizaje.js')
        self.assertContains(response, 'font-awesome')
    
    def test_progress_tracking(self):
        """Test seguimiento de progreso"""
        # Completar lección
        self.client.post(f'/aprendizaje/leccion/{self.leccion.id}/completar/')
        
        # Verificar en dashboard
        response = self.client.get('/aprendizaje/')
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el progreso se muestra
        progreso = ProgresoUsuario.objects.get(
            usuario=self.user,
            leccion=self.leccion
        )
        self.assertTrue(progreso.completada)
    
    def test_xp_counter_display(self):
        """Test que el contador de XP se muestra"""
        response = self.client.get(f'/aprendizaje/leccion/{self.leccion.id}/')
        
        self.assertContains(response, 'xp-counter')
        self.assertContains(response, 'fas fa-star')
    
    def test_responsive_design_elements(self):
        """Test elementos de diseño responsivo"""
        response = self.client.get(f'/aprendizaje/leccion/{self.leccion.id}/')
        
        # Verificar clases Bootstrap y CSS custom
        self.assertContains(response, 'academia-container')
        self.assertContains(response, 'academia-header')
        self.assertContains(response, 'paso-item')
        self.assertContains(response, 'btn-duolingo')