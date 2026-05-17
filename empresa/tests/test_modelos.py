"""
Tests fundamentales para los modelos de Contafy.

Verifica:
- Creación básica de los modelos principales
- Campos obligatorios
- Relaciones entre modelos
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from empresa.models import (
    Usuario, Empresa, Producto, Venta, Compra, Gasto,
    CuentaContable, MovimientoContable, Capital,
)


@pytest.mark.django_db
class TestUsuarioModel(TestCase):
    """Tests para el modelo Usuario (AUTH_USER_MODEL personalizado)."""

    def test_crear_usuario_basico(self):
        """Un usuario se crea con username y password."""
        user = Usuario.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Juan',
            last_name='Perez',
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertIsNotNone(user.pk)

    def test_usuario_str(self):
        """__str__ del usuario devuelve algo legible."""
        user = Usuario.objects.create_user(username='maria', password='pass123')
        self.assertTrue(str(user))  # No debe ser vacío


@pytest.mark.django_db
class TestEmpresaModel(TestCase):
    """Tests para el modelo Empresa."""

    def setUp(self):
        self.user = Usuario.objects.create_user(
            username='owner', password='pass123'
        )

    def test_crear_empresa(self):
        """Una empresa se crea con nombre, ruc y categoría."""
        empresa = Empresa.objects.create(
            nombre='Mi Tienda',
            ruc='1790016919001',
            direccion='Quito, Ecuador',
            categoria='comercial',
        )
        self.assertEqual(empresa.nombre, 'Mi Tienda')
        self.assertEqual(empresa.categoria, 'comercial')
        self.assertIsNotNone(empresa.pk)

    def test_empresa_str(self):
        empresa = Empresa.objects.create(
            nombre='Test Corp', ruc='1791234567001', direccion='Guayaquil',
            categoria='servicios',
        )
        self.assertIn('Test Corp', str(empresa))

    def test_empresa_categorias_validas(self):
        """Las categorías válidas son: comercial, manufactura, servicios."""
        rucs = ['1790016919001', '1791234567001', '1792345678001']
        for cat, ruc in zip(['comercial', 'manufactura', 'servicios'], rucs):
            empresa = Empresa.objects.create(
                nombre=f'Empresa {cat}', ruc=ruc, direccion='Ecuador',
                categoria=cat,
            )
            self.assertEqual(empresa.categoria, cat)

    def test_empresa_relacion_propietario(self):
        """Una empresa puede tener un propietario."""
        empresa = Empresa.objects.create(
            nombre='Con Dueño', ruc='1793456789001', direccion='Cuenca',
            categoria='comercial', propietario=self.user,
        )
        self.assertEqual(empresa.propietario, self.user)


@pytest.mark.django_db
class TestProductoModel(TestCase):
    """Tests para el modelo Producto."""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Tienda Test', ruc='1790016919001', direccion='Quito',
            categoria='comercial',
        )

    def test_crear_producto(self):
        producto = Producto.objects.create(
            empresa=self.empresa,
            nombre='Laptop HP',
            precio_unitario=Decimal('800.00'),
            pvp=Decimal('1000.00'),
            stock=10,
            codigo='PROD-001',
        )
        self.assertEqual(producto.nombre, 'Laptop HP')
        self.assertEqual(producto.stock, 10)
        self.assertEqual(producto.empresa, self.empresa)

    def test_producto_requiere_empresa(self):
        """Un producto sin empresa debe fallar."""
        with self.assertRaises((IntegrityError, ValidationError)):
            Producto.objects.create(
                nombre='Sin Empresa',
                precio_unitario=Decimal('10.00'),
                pvp=Decimal('15.00'),
                stock=1,
                codigo='PROD-NO-EMP',
            )

    def test_producto_relacion_empresa(self):
        """Los productos se acceden desde la empresa."""
        Producto.objects.create(
            empresa=self.empresa,
            nombre='Teclado',
            precio_unitario=Decimal('25.00'),
            pvp=Decimal('35.00'),
            stock=50,
            codigo='PROD-002',
        )
        productos = Producto.objects.filter(empresa=self.empresa)
        self.assertEqual(productos.count(), 1)
        self.assertEqual(productos.first().nombre, 'Teclado')


@pytest.mark.django_db
class TestVentaModel(TestCase):
    """Tests para el modelo Venta."""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Tienda Ventas', ruc='1790016919001', direccion='Quito',
            categoria='comercial',
        )
        self.user = Usuario.objects.create_user(
            username='vendedor', password='pass123', empresa=self.empresa
        )
        self.producto = Producto.objects.create(
            empresa=self.empresa,
            nombre='Mouse',
            precio_unitario=Decimal('10.00'),
            pvp=Decimal('15.00'),
            stock=100,
            codigo='VENTA-PROD-001',
        )

    def test_crear_venta_contado(self):
        venta = Venta.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            cantidad=2,
            monto_neto=Decimal('30.00'),
            tasa_iva=Decimal('15'),
            iva=Decimal('4.50'),
            monto=Decimal('34.50'),
            tipo_pago='contado',
        )
        self.assertEqual(venta.cantidad, 2)
        self.assertEqual(venta.monto, Decimal('34.50'))

    def test_venta_calcula_iva_desde_neto(self):
        """Si solo se da monto_neto, el IVA se calcula automáticamente."""
        venta = Venta.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            cantidad=1,
            monto_neto=Decimal('100.00'),
            tasa_iva=Decimal('15'),
            monto=Decimal('0'),  # Se calculará
            tipo_pago='contado',
        )
        self.assertEqual(venta.iva, Decimal('15.00'))
        self.assertEqual(venta.monto, Decimal('115.00'))

    def test_venta_relacion_producto(self):
        venta = Venta.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            cantidad=1,
            monto_neto=Decimal('15.00'),
            tasa_iva=Decimal('15'),
            iva=Decimal('2.25'),
            monto=Decimal('17.25'),
            tipo_pago='contado',
        )
        self.assertEqual(venta.producto.nombre, 'Mouse')


@pytest.mark.django_db
class TestCompraModel(TestCase):
    """Tests para el modelo Compra."""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Tienda Compras', ruc='1790016919001', direccion='Quito',
            categoria='comercial',
        )
        self.producto = Producto.objects.create(
            empresa=self.empresa,
            nombre='Monitor',
            precio_unitario=Decimal('200.00'),
            pvp=Decimal('280.00'),
            stock=5,
            codigo='COMPRA-PROD-001',
        )

    def test_crear_compra(self):
        compra = Compra.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            cantidad=3,
            monto_neto=Decimal('600.00'),
            tasa_iva=Decimal('15'),
            iva=Decimal('90.00'),
            monto=Decimal('690.00'),
            tipo_pago='contado',
        )
        self.assertEqual(compra.cantidad, 3)
        self.assertEqual(compra.monto, Decimal('690.00'))


@pytest.mark.django_db
class TestGastoModel(TestCase):
    """Tests para el modelo Gasto."""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Gastos', ruc='1790016919001', direccion='Quito',
            categoria='servicios',
        )

    def test_crear_gasto(self):
        gasto = Gasto.objects.create(
            empresa=self.empresa,
            descripcion='Alquiler oficina',
            monto=Decimal('500.00'),
            tipo_pago='contado',
        )
        self.assertEqual(gasto.descripcion, 'Alquiler oficina')
        self.assertEqual(gasto.monto, Decimal('500.00'))

    def test_gasto_requiere_empresa(self):
        with self.assertRaises((IntegrityError, ValidationError)):
            Gasto.objects.create(
                descripcion='Sin empresa',
                monto=Decimal('100.00'),
                tipo_pago='contado',
            )


@pytest.mark.django_db
class TestCuentaContableModel(TestCase):
    """Tests para cuentas contables."""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Contable Test', ruc='1790016919001', direccion='Quito',
            categoria='comercial',
        )

    def test_crear_cuenta(self):
        cuenta = CuentaContable.objects.create(
            empresa=self.empresa,
            nombre='Caja',
            tipo='activo',
        )
        self.assertEqual(cuenta.nombre, 'Caja')
        self.assertEqual(cuenta.tipo, 'activo')

    def test_tipos_cuenta(self):
        """Los tipos válidos de cuenta son: activo, pasivo, capital, ingreso, gasto."""
        for tipo in ['activo', 'pasivo', 'capital', 'ingreso', 'gasto']:
            cuenta = CuentaContable.objects.create(
                empresa=self.empresa,
                nombre=f'Cuenta {tipo}',
                tipo=tipo,
            )
            self.assertEqual(cuenta.tipo, tipo)
