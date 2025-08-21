from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario
import json

User = get_user_model()


class SimulacionSandboxRecetaTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester_receta', password='pass')
        self.client.login(username='tester_receta', password='pass')
        # Crear tipo de simulación de receta
        self.tipo = TipoSimulacion.objects.create(
            nombre='Simulación de Receta', categoria='manufactura', descripcion='test'
        )

    def test_sandbox_receta_no_persiste_movimientos(self):
        ingredientes = [
            {'nombre': 'A', 'cantidad': 1, 'precio_unitario': 2.0},
            {'nombre': 'B', 'cantidad': 2, 'precio_unitario': 1.5},
        ]

        data = {
            'producto_nombre': 'ProductoX',
            'ingredientes': json.dumps(ingredientes),
            'costo_total': '5.0',
            'precio_venta': '7.0',
        }

        url = reverse('empresa:simulacion_receta')
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        content = resp.json()
        self.assertIn('exito', content)
        self.assertIn('puntuacion', content)

        sims = SimulacionUsuario.objects.filter(usuario=self.user, tipo_simulacion=self.tipo)
        self.assertTrue(sims.exists())
        self.assertTrue(sims.last().es_sandbox)
