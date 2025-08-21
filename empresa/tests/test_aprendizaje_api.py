from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from empresa.models_simulaciones import TipoSimulacion, EscenarioSimulacion, SimulacionUsuario

User = get_user_model()


class AprendizajeApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='apiuser', password='pass')
        self.client.login(username='apiuser', password='pass')

    def test_simulacion_escenarios_api_returns_escenarios(self):
        tipo = TipoSimulacion.objects.create(nombre='Tipo A', categoria='comercial', descripcion='d')
        e1 = EscenarioSimulacion.objects.create(tipo_simulacion=tipo, nombre='Esc1', descripcion='x', datos_iniciales={'a':1}, solucion_esperada={}, dificultad=1, puntos_max=50)
        e2 = EscenarioSimulacion.objects.create(tipo_simulacion=tipo, nombre='Esc2', descripcion='y', datos_iniciales={'b':2}, solucion_esperada={}, dificultad=2, puntos_max=80)

        url = reverse('empresa:simulacion_escenarios_api') + f'?tipo_id={tipo.id}'
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get('ok'))
        esc = data.get('escenarios')
        self.assertIsInstance(esc, list)
        names = {e['nombre'] for e in esc}
        self.assertSetEqual(names, {e1.nombre, e2.nombre})

    def test_simulacion_start_api_creates_simulation_without_escenario(self):
        tipo = TipoSimulacion.objects.create(nombre='Tipo B', categoria='comercial', descripcion='d')
        url = reverse('empresa:simulacion_start_api')
        payload = {'tipo_id': tipo.id}
        r = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get('ok'))
        sim_id = data.get('simulacion_id')
        sim = SimulacionUsuario.objects.get(id=sim_id)
        self.assertEqual(sim.tipo_simulacion.id, tipo.id)

    def test_simulacion_start_api_with_escenario_attaches_data(self):
        tipo = TipoSimulacion.objects.create(nombre='Tipo C', categoria='comercial', descripcion='d')
        escenario = EscenarioSimulacion.objects.create(tipo_simulacion=tipo, nombre='EscData', descripcion='z', datos_iniciales={'x': 42}, solucion_esperada={}, dificultad=1, puntos_max=100)
        url = reverse('empresa:simulacion_start_api')
        payload = {'tipo_id': tipo.id, 'escenario_id': escenario.id}
        r = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('datos_iniciales'), {'x': 42})
        sim = SimulacionUsuario.objects.get(id=data.get('simulacion_id'))
        self.assertEqual(sim.datos_entrada, {'x': 42})
