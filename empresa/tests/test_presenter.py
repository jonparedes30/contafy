import unittest
from empresa.presenters.resumen_presenter import ResumenPresenter


class TestResumenPresenter(unittest.TestCase):
    def test_normaliza_contexto_vacio(self):
        presenter = ResumenPresenter(empresa=None, data={})
        ctx = presenter.to_context()
        # Valores por defecto
        self.assertEqual(ctx['ventas'], 0.0)
        self.assertEqual(ctx['compras'], 0.0)
        self.assertEqual(ctx['gastos'], 0.0)
        self.assertIsInstance(ctx['kpis'], list)

    def test_kpis_valores(self):
        data = {'ventas': 1000, 'compras': 200, 'gastos': 100, 'utilidad_neta': 700}
        presenter = ResumenPresenter(empresa=None, data=data)
        ctx = presenter.to_context()
        self.assertAlmostEqual(ctx['ventas'], 1000.0)
        self.assertAlmostEqual(ctx['utilidad_neta'], 700.0)
        self.assertEqual(len(ctx['kpis']), 4)


if __name__ == '__main__':
    unittest.main()
