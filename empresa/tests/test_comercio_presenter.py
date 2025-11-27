"""Tests para ComercioPresenter"""
from django.test import TestCase, RequestFactory
from empresa.models import Empresa, Producto, Cliente, Venta
from empresa.presenters.comercio_presenter import ComercioPresenter


class ComercioPresenterTest(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Test Comercio',
            ruc='1234567890123',
            categoria='comercial',
            tipo_negocio='Retail'
        )

    def test_context_con_datos_vacios(self):
        """Presenter debe devolver contexto seguro incluso sin productos"""
        presenter = ComercioPresenter(self.empresa)
        context = presenter.to_context()

        self.assertEqual(context['total_productos'], 0)
        self.assertEqual(context['productos_stock_bajo'], [])
        self.assertEqual(context['top_productos_volumen'], [])
        self.assertEqual(context['total_ventas'], 0.0)
        self.assertEqual(context['margen_bruto_pct'], 0.0)

    def test_context_con_productos(self):
        """Presenter debe calcular correctamente con productos existentes"""
        # Crear productos
        p1 = Producto.objects.create(
            empresa=self.empresa,
            nombre='Producto Test 1',
            codigo='P001',
            precio_unitario=150.0,
            stock=50,
            stock_minimo=10,
            activo=True
        )
        p2 = Producto.objects.create(
            empresa=self.empresa,
            nombre='Producto Test 2',
            codigo='P002',
            precio_unitario=300.0,
            stock=5,  # Bajo stock
            stock_minimo=10,
            activo=True
        )

        presenter = ComercioPresenter(self.empresa)
        context = presenter.to_context()

        self.assertEqual(context['total_productos'], 2)
        self.assertEqual(len(context['productos_stock_bajo']), 1)
        self.assertIn(p2, context['productos_stock_bajo'])

    def test_num_helper(self):
        """Helper _num debe convertir valores seguramente"""
        presenter = ComercioPresenter(self.empresa)

        self.assertEqual(presenter._num(100), 100.0)
        self.assertEqual(presenter._num('200'), 200.0)
        self.assertEqual(presenter._num(None), 0.0)
        self.assertEqual(presenter._num('invalid'), 0.0)
        self.assertEqual(presenter._num(None, 50), 50.0)
