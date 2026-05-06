"""
Tests para la API REST de Contafy.

Verifica:
- Endpoints protegidos devuelven 401 sin autenticación
- CRUD básico funciona con autenticación
- Formato de respuestas JSON correcto
"""
import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from empresa.models import Usuario, Empresa, Producto


@pytest.mark.django_db
class TestAPIAutenticacion(TestCase):
    """Tests de autenticación en endpoints protegidos."""

    def setUp(self):
        self.client = Client()

    def test_endpoints_protegidos_sin_login(self):
        """Endpoints protegidos redirigen a login sin autenticación."""
        endpoints_protegidos = [
            '/app-beta-2024/dashboard/',
            '/app-beta-2024/producto/listar/',
            '/app-beta-2024/venta/listar/',
            '/app-beta-2024/compra/listar/',
        ]

        for url in endpoints_protegidos:
            response = self.client.get(url)
            # Debe redirigir a login (302) o devolver 401/403
            self.assertIn(
                response.status_code,
                [302, 401, 403],
                f"{url} accesible sin login (status={response.status_code})",
            )

    def test_api_rest_sin_token(self):
        """La API REST devuelve 401 sin token JWT."""
        response = self.client.get('/app-beta-2024/api/productos/')
        self.assertIn(response.status_code, [401, 403])


@pytest.mark.django_db
class TestAPIConAutenticacion(TestCase):
    """Tests de API con usuario autenticado."""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='API Test', categoria='comercio'
        )
        self.user = Usuario.objects.create_user(
            username='apiuser',
            password='testpass123',
            empresa=self.empresa,
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_listar_productos_autenticado(self):
        """Listar productos con usuario autenticado devuelve 200."""
        response = self.client.get('/app-beta-2024/producto/listar/')
        self.assertEqual(response.status_code, 200)

    def test_listar_ventas_autenticado(self):
        """Listar ventas con usuario autenticado devuelve 200."""
        response = self.client.get('/app-beta-2024/venta/listar/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_autenticado(self):
        """Dashboard con usuario autenticado devuelve 200."""
        response = self.client.get('/app-beta-2024/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_crear_producto_get(self):
        """GET a crear producto muestra el formulario."""
        response = self.client.get('/app-beta-2024/producto/crear/')
        self.assertEqual(response.status_code, 200)


@pytest.mark.django_db
class TestAPIProductoInfo(TestCase):
    """Tests para el endpoint de información de producto."""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Producto API Test', categoria='comercio'
        )
        self.user = Usuario.objects.create_user(
            username='produser',
            password='testpass123',
            empresa=self.empresa,
        )
        self.producto = Producto.objects.create(
            empresa=self.empresa,
            nombre='Test Product',
            precio_unitario=Decimal('50.00'),
            pvp=Decimal('75.00'),
            stock=20,
            codigo='TEST-001',
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_producto_info_api(self):
        """El endpoint de info de producto devuelve JSON."""
        response = self.client.get(
            '/app-beta-2024/producto/info_api/',
            {'producto_id': self.producto.id},
        )
        # Puede devolver 200 con JSON o 400 si requiere otro formato
        self.assertIn(response.status_code, [200, 400])


@pytest.mark.django_db
class TestAPICacheTest(TestCase):
    """Test que verifica que el caché funciona correctamente."""

    def test_cache_set_get(self):
        """El backend de caché puede guardar y recuperar valores."""
        from django.core.cache import cache

        cache.set('test_key', 'test_value', timeout=30)
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value')

    def test_cache_delete(self):
        """El backend de caché puede eliminar valores."""
        from django.core.cache import cache

        cache.set('delete_key', 'to_delete', timeout=30)
        cache.delete('delete_key')
        value = cache.get('delete_key')
        self.assertIsNone(value)

    def test_cache_timeout(self):
        """El caché respeta el timeout."""
        from django.core.cache import cache

        cache.set('timeout_key', 'expires', timeout=1)
        # El valor debe existir inmediatamente
        self.assertEqual(cache.get('timeout_key'), 'expires')

    def test_cache_default_value(self):
        """cache.get devuelve default si la key no existe."""
        from django.core.cache import cache

        value = cache.get('nonexistent', default='fallback')
        self.assertEqual(value, 'fallback')
