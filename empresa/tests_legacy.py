from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal

from .models import Empresa, Producto, Venta
from .validators import validar_ruc_ecuador
from .utils.security import LoginAttemptTracker

User = get_user_model()


class ValidatorsTestCase(TestCase):
    """Tests para validadores"""
    
    def test_ruc_valido(self):
        """Test RUC válido"""
        try:
            validar_ruc_ecuador('1792146739001')
        except Exception:
            self.fail("RUC válido no debería fallar")
    
    def test_ruc_invalido(self):
        """Test RUC inválido"""
        with self.assertRaises(Exception):
            validar_ruc_ecuador('1234567890123')


class SecurityTestCase(TestCase):
    """Tests de seguridad"""
    
    def setUp(self):
        self.client = Client()
        self.empresa = Empresa.objects.create(
            nombre="Test Empresa",
            ruc="1792146739001",
            direccion="Test Address"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            empresa=self.empresa
        )
    
    def test_login_rate_limiting(self):
        """Test rate limiting en login"""
        login_url = reverse('empresa:login')
        
        # Simular 5 intentos fallidos
        for i in range(5):
            response = self.client.post(login_url, {
                'username': 'wronguser',
                'password': 'wrongpass'
            })
        
        # El sexto intento debería ser bloqueado
        response = self.client.post(login_url, {
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        
        self.assertEqual(response.status_code, 429)
    
    def test_successful_login(self):
        """Test login exitoso"""
        login_url = reverse('empresa:login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertRedirects(response, reverse('empresa:home'))


class ModelTestCase(TestCase):
    """Tests para modelos"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre="Test Empresa",
            ruc="1792146739001",
            direccion="Test Address"
        )
        self.producto = Producto.objects.create(
            empresa=self.empresa,
            codigo="TEST001",
            nombre="Producto Test",
            precio_unitario=Decimal('10.00'),
            stock=100
        )
    
    def test_empresa_creation(self):
        """Test creación de empresa"""
        self.assertEqual(self.empresa.nombre, "Test Empresa")
        self.assertEqual(str(self.empresa), "Test Empresa")
    
    def test_producto_creation(self):
        """Test creación de producto"""
        self.assertEqual(self.producto.codigo, "TEST001")
        self.assertEqual(self.producto.empresa, self.empresa)
    
    def test_venta_calculation(self):
        """Test cálculo de venta"""
        venta = Venta.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            cantidad=5,
            precio_unitario=Decimal('10.00'),
            total=Decimal('50.00')
        )
        
        self.assertEqual(venta.total, Decimal('50.00'))
        self.assertEqual(venta.cantidad * venta.precio_unitario, venta.total)
