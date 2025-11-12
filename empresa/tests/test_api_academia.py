from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from empresa.models import Empresa
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario

User = get_user_model()

class AcademiaAPITests(TestCase):
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
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
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
            pasos=[{'titulo': 'Paso 1', 'descripcion': 'Test'}]
        )
        self.tipo_simulacion = TipoSimulacion.objects.create(
            nombre='Test Simulación',
            categoria='comercial',
            descripcion='Test'
        )
    
    def test_modulos_list_api(self):
        """Test API de lista de módulos"""
        url = reverse('api:modulos-list')
        response = self.client.get(url, {'tipo_empresa': 'comercial'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Con paginación, la respuesta tiene estructura diferente
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['nombre'], 'Módulo Test')
        else:
            # Fallback sin paginación
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['nombre'], 'Módulo Test')
    
    def test_lecciones_list_api(self):
        """Test API de lista de lecciones"""
        url = reverse('api:lecciones-list')
        response = self.client.get(url, {'modulo_id': self.modulo.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Con paginación, la respuesta tiene estructura diferente
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['titulo'], 'Lección Test')
        else:
            # Fallback sin paginación
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['titulo'], 'Lección Test')
    
    def test_leccion_detail_api(self):
        """Test API de detalle de lección"""
        url = reverse('api:leccion-detail', kwargs={'leccion_id': self.leccion.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['titulo'], 'Lección Test')
        self.assertIn('pasos', response.data)
    
    def test_simulacion_start_api(self):
        """Test API de inicio de simulación"""
        url = reverse('api:simulacion-start')
        data = {
            'tipo_simulacion_id': self.tipo_simulacion.id,
            'leccion_id': self.leccion.id,
            'modo_sandbox': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['estado'], 'iniciada')
        self.assertTrue(response.data['es_sandbox'])
    
    def test_simulacion_detail_api(self):
        """Test API de detalle de simulación"""
        simulacion = SimulacionUsuario.objects.create(
            usuario=self.user,
            tipo_simulacion=self.tipo_simulacion,
            leccion=self.leccion,
            es_sandbox=True
        )
        
        url = reverse('api:simulacion-detail', kwargs={'simulacion_id': simulacion.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], simulacion.id)
    
    def test_simulacion_guardar_api(self):
        """Test API de guardar progreso de simulación"""
        simulacion = SimulacionUsuario.objects.create(
            usuario=self.user,
            tipo_simulacion=self.tipo_simulacion,
            es_sandbox=True
        )
        
        url = reverse('api:simulacion-guardar', kwargs={'simulacion_id': simulacion.id})
        data = {
            'datos_usuario': {
                'producto': 'Test Product',
                'cantidad': 1,
                'precio': 100.00
            }
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'guardado')
    
    def test_simulacion_finalizar_api(self):
        """Test API de finalizar simulación"""
        simulacion = SimulacionUsuario.objects.create(
            usuario=self.user,
            tipo_simulacion=self.tipo_simulacion,
            leccion=self.leccion,
            es_sandbox=True
        )
        
        url = reverse('api:simulacion-finalizar', kwargs={'simulacion_id': simulacion.id})
        data = {
            'datos_usuario': {
                'producto': 'Test Product',
                'cantidad': 1,
                'precio_unitario': 100.00,
                'subtotal': 100.00,
                'iva': 12.00,
                'total': 112.00
            }
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resultado', response.data)
        self.assertIn('simulacion', response.data)
    
    def test_progreso_usuario_api(self):
        """Test API de progreso del usuario"""
        url = reverse('api:progreso-usuario')
        response = self.client.get(url, {'tipo_empresa': 'comercial'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_recomendaciones_api(self):
        """Test API de recomendaciones"""
        url = reverse('api:recomendaciones')
        response = self.client.get(url, {'limite': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_api_requires_authentication(self):
        """Test que las APIs requieren autenticación"""
        self.client.force_authenticate(user=None)
        
        url = reverse('api:modulos-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)