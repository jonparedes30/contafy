"""Regresiones del cobro en el punto de venta (crear_venta_multiple)."""
import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from empresa.models import Empresa, Producto, Venta

User = get_user_model()


class CobroPOSTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre="Tienda POS", ruc="1792146739001", direccion="Quito", categoria="comercio"
        )
        self.user = User.objects.create_user(username="cajero", password="x", empresa=self.empresa)
        self.empresa.propietario = self.user
        self.empresa.save()
        self.coca = Producto.objects.create(
            empresa=self.empresa, codigo="BEB001", nombre="Coca Cola 2L",
            precio_unitario=Decimal('1.20'), pvp=Decimal('1.80'), stock=10,
        )
        self.doritos = Producto.objects.create(
            empresa=self.empresa, codigo="SNK001", nombre="Doritos",
            precio_unitario=Decimal('1.00'), pvp=Decimal('1.50'), stock=1,
        )
        self.client.force_login(self.user)
        self.url = reverse('empresa:crear_venta_multiple')

    def _cobrar(self, productos, recibido, tipo_pago='contado'):
        resp = self.client.post(self.url, data=json.dumps({
            'productos': productos, 'tipo_pago': tipo_pago, 'monto_recibido': recibido,
        }), content_type='application/json')
        return resp.json()

    def test_monto_insuficiente_no_registra_venta_ni_descuenta_stock(self):
        data = self._cobrar([{'id': self.coca.id, 'cantidad': 3, 'precio': '1.80'}], recibido='0')
        self.assertFalse(data['success'])
        self.assertIn('Monto insuficiente', data['error'])
        self.assertEqual(Venta.objects.filter(empresa=self.empresa).count(), 0)
        self.coca.refresh_from_db()
        self.assertEqual(self.coca.stock, 10)

    def test_stock_insuficiente_en_segundo_producto_deshace_el_primero(self):
        data = self._cobrar([
            {'id': self.coca.id, 'cantidad': 2, 'precio': '1.80'},
            {'id': self.doritos.id, 'cantidad': 5, 'precio': '1.50'},
        ], recibido='100')
        self.assertFalse(data['success'])
        self.assertIn('Stock insuficiente', data['error'])
        self.assertEqual(Venta.objects.filter(empresa=self.empresa).count(), 0)
        self.coca.refresh_from_db()
        self.assertEqual(self.coca.stock, 10)

    def test_cobro_correcto_calcula_cambio_exacto(self):
        data = self._cobrar([
            {'id': self.coca.id, 'cantidad': 3, 'precio': '1.80'},
            {'id': self.doritos.id, 'cantidad': 1, 'precio': '1.50'},
        ], recibido='10,00')
        self.assertTrue(data['success'], data)
        self.assertEqual(data['total'], 6.90)
        self.assertEqual(data['cambio'], 3.10)
        self.assertEqual(Venta.objects.filter(empresa=self.empresa).count(), 2)
        self.coca.refresh_from_db()
        self.assertEqual(self.coca.stock, 7)

    def test_cantidad_cero_es_rechazada(self):
        data = self._cobrar([{'id': self.coca.id, 'cantidad': 0, 'precio': '1.80'}], recibido='5')
        self.assertFalse(data['success'])
        self.assertEqual(Venta.objects.filter(empresa=self.empresa).count(), 0)
