from django.test import TestCase, Client
from django.urls import reverse
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from empresa.models import Venta, Gasto, MovimientoContable
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario
import json

User = get_user_model()


class SimulacionSandboxTest(TestCase):
    def setUp(self):
        # Usuario y cliente
        self.user = User.objects.create_user(username='sandboxuser', password='pass')
        self.client = Client()
        self.client.login(username='sandboxuser', password='pass')

        # Crear módulo y lección tipo 'practica'
        self.mod = ModuloAprendizaje.objects.create(
            nombre='Módulo sandbox', tipo_empresa='comercial', descripcion='d', orden=1, activo=True
        )
        self.leccion = Leccion.objects.create(
            modulo=self.mod, titulo='Lección sandbox', tipo='practica', puntos_xp=10, activa=True
        )

        # Crear tipos de simulación simples
        self.tipo_venta = TipoSimulacion.objects.create(
            nombre='Simulación de Venta', categoria='comercial', descripcion='venta demo'
        )

    def test_sandbox_venta_no_persiste_movimientos(self):
        # Contar registros antes
        ventas_before = Venta.objects.count()
        gastos_before = Gasto.objects.count()
        mov_before = MovimientoContable.objects.count()
        sim_before = SimulacionUsuario.objects.count()

        # Iniciar simulación via endpoint (start)
        start_url = reverse('empresa:simulacion_start_api')
        resp = self.client.post(
            start_url,
            data=json.dumps({'tipo_id': self.tipo_venta.id, 'leccion_id': self.leccion.id}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('ok'))
        sim_id = data.get('simulacion_id')
        self.assertIsNotNone(sim_id)

        # Ejecutar POST a simulacion_venta endpoint with payload that would create a venta
        sim_url = reverse('empresa:simulacion_venta_leccion', args=[self.leccion.id])
        # Construir payload que coincida con lo que espera SimulacionService
        cantidad = 2
        precio_unitario = 15.0
        subtotal = cantidad * precio_unitario
        iva = round(subtotal * 0.12, 2)
        total = round(subtotal + iva, 2)

        payload = {
            'cliente': 'Cliente Demo',
            'producto': 'Camiseta',
            'cantidad': str(cantidad),
            'precio_unitario': str(precio_unitario),
            'subtotal': str(subtotal),
            'iva': str(iva),
            'total': str(total)
        }

        resp2 = self.client.post(sim_url, data=payload)
        self.assertEqual(resp2.status_code, 200)
        resultado = resp2.json()
        # Debe devolver resultado con clave 'exito' y ser exitoso
        self.assertIn('exito', resultado)
        self.assertTrue(resultado.get('exito'))

        # Verificar que no se crearon ventas/gastos/movimientos reales
        self.assertEqual(Venta.objects.count(), ventas_before)
        self.assertEqual(Gasto.objects.count(), gastos_before)
        self.assertEqual(MovimientoContable.objects.count(), mov_before)

        # Pero sí debe existir una SimulacionUsuario creada
        self.assertGreaterEqual(SimulacionUsuario.objects.count(), sim_before + 1)
