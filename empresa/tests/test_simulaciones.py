from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from empresa.management.commands.crear_simulaciones import Command as CrearSimCommand
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario
import json

User = get_user_model()


class SimulacionesTests(TestCase):
    def setUp(self):
        # Crear tipos de simulación
        cmd = CrearSimCommand()
        cmd.handle()
        self.user = User.objects.create_user(username='sim', password='pass')
        self.client = Client()
        self.client.login(username='sim', password='pass')
        self.tipo = TipoSimulacion.objects.filter(nombre='Simulación de Venta').first()

    def test_iniciar_y_procesar_simulacion_venta_valida(self):
        # Iniciar simulación vía servicio
        from empresa.services.simulacion_service import SimulacionService
        simulacion = SimulacionService.iniciar_simulacion(self.user, self.tipo.id)
        datos = {
            'producto': 'Camiseta',
            'cantidad': 2,
            'precio_unitario': 15.00,
            'subtotal': 30.00,
            'iva': 3.6,
            'total': 33.6,
            'cliente': 'Cliente prueba'
        }
        resultado = SimulacionService.procesar_simulacion_venta(simulacion, datos)
        self.assertTrue(resultado.get('exito'))
        self.assertGreaterEqual(resultado.get('puntuacion', 0), 60)
        sim_db = SimulacionUsuario.objects.get(id=simulacion.id)
        self.assertEqual(sim_db.estado, 'completada')

    def test_procesar_simulacion_venta_invalida(self):
        from empresa.services.simulacion_service import SimulacionService
        simulacion = SimulacionService.iniciar_simulacion(self.user, self.tipo.id)
        datos = {
            'producto': '',
            'cantidad': 0,
            'precio_unitario': 0,
        }
        resultado = SimulacionService.procesar_simulacion_venta(simulacion, datos)
        self.assertFalse(resultado.get('exito'))
        sim_db = SimulacionUsuario.objects.get(id=simulacion.id)
        self.assertEqual(sim_db.estado, 'fallida')
