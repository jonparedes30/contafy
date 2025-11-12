from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from empresa.models import Empresa, Producto, Venta
from empresa.validators import validar_ruc_ecuador

User = get_user_model()


class ValidatorsTestCase(TestCase):
    def test_ruc_valido(self):
        try:
            validar_ruc_ecuador('1792146739001')
        except Exception:
            self.fail("RUC válido no debería fallar")

    def test_ruc_invalido(self):
        with self.assertRaises(Exception):
            validar_ruc_ecuador('1234567890123')


class ModelTestCase(TestCase):
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
        self.assertEqual(self.empresa.nombre, "Test Empresa")
        self.assertEqual(str(self.empresa), "Test Empresa")

    def test_producto_creation(self):
        self.assertEqual(self.producto.codigo, "TEST001")
        self.assertEqual(self.producto.empresa, self.empresa)

    def test_venta_calculation(self):
        venta = Venta.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            cantidad=5,
            precio_unitario=Decimal('10.00'),
            total=Decimal('50.00')
        )
        self.assertEqual(venta.total, Decimal('50.00'))
        self.assertEqual(venta.cantidad * venta.precio_unitario, venta.total)
