from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario

User = get_user_model()


class SimulacionSandboxServicioTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester_servicio', password='pass')
        self.client.login(username='tester_servicio', password='pass')
        # Crear tipo de simulación de servicio
        self.tipo = TipoSimulacion.objects.create(
            nombre='Simulación de Servicio', categoria='servicios', descripcion='test'
        )

    def test_sandbox_servicio_no_persiste_movimientos(self):
        data = {
            'tipo_servicio': 'Consultoría',
            'horas_trabajadas': '2',
            'tarifa_hora': '30',
            'gastos_adicionales': '0',
            'subtotal': '60',
            'iva': '7.2',
            'total': '67.2',
        }

        url = reverse('empresa:simulacion_servicio')
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        content = resp.json()
        self.assertIn('exito', content)
        self.assertIn('puntuacion', content)

        sims = SimulacionUsuario.objects.filter(usuario=self.user, tipo_simulacion=self.tipo)
        self.assertTrue(sims.exists())
        self.assertTrue(sims.last().es_sandbox)
