"""Tests para ServicioPresenter"""
from django.test import TestCase
from empresa.models import Empresa, Cliente, Venta
from empresa.presenters.servicio_presenter import ServicioPresenter


class ServicioPresenterTest(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Test Servicio',
            ruc='9876543210987',
            categoria='servicios',
            tipo_negocio='Consultoría'
        )

    def test_context_con_datos_vacios(self):
        """Presenter debe devolver contexto seguro sin clientes"""
        presenter = ServicioPresenter(self.empresa)
        context = presenter.to_context()

        self.assertEqual(context['ordenes_totales'], 0)
        self.assertEqual(context['clientes_activos'], 0)
        self.assertEqual(context['total_clientes'], 0)
        self.assertEqual(context['total_ingresos'], 0.0)
        self.assertEqual(context['valor_promedio_servicio'], 0.0)

    def test_num_helper(self):
        """Helper _num debe convertir valores seguramente"""
        presenter = ServicioPresenter(self.empresa)

        self.assertEqual(presenter._num(500), 500.0)
        self.assertEqual(presenter._num('750'), 750.0)
        self.assertEqual(presenter._num(None), 0.0)
        self.assertEqual(presenter._num('bad_value'), 0.0)
        self.assertEqual(presenter._num(None, 100), 100.0)

    def test_presenter_minimo_no_error(self):
        """Presenter no debe lanzar excepciones incluso con pocos datos"""
        # Crear cliente y venta mínimos
        cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            ruc='1111111111111'
        )
        venta = Venta.objects.create(
            empresa=self.empresa,
            cliente_fk=cliente,
            producto=None,  # Opcional para servicios
            cantidad=1,
            precio_unitario=1000.0,
            monto=1000.0
        )

        presenter = ServicioPresenter(self.empresa)
        context = presenter.to_context()

        # No debe lanzar excepción
        self.assertIsNotNone(context)
        self.assertEqual(context['ordenes_totales'], 1)
        self.assertIn('total_ingresos', context)
