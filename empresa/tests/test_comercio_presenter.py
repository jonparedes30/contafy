"""Tests para ComercioPresenter"""
from django.test import TestCase
from empresa.models import Empresa
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

    def test_num_helper(self):
        """Helper _num debe convertir valores seguramente"""
        presenter = ComercioPresenter(self.empresa)

        self.assertEqual(presenter._num(100), 100.0)
        self.assertEqual(presenter._num('200'), 200.0)
        self.assertEqual(presenter._num(None), 0.0)
        self.assertEqual(presenter._num('invalid'), 0.0)
        self.assertEqual(presenter._num(None, 50), 50.0)
