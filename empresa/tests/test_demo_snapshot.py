"""Regla de las demos: lo que hace un visitante no se conserva; cada 24 h vuelve la foto original."""
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from empresa.models import DemoSnapshot, Empresa, PoderEmpleado, Producto, Venta
from empresa.services.demo_snapshot import guardar_foto, restaurar, restaurar_si_vencida

User = get_user_model()


class DemoSnapshotTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Minimarket Demo', ruc='1792146739001',
                                              direccion='Quito', categoria='comercial')
        self.dueno = User.objects.create_user(username='demo_comercio', password='x', empresa=self.empresa)
        self.empresa.propietario = self.dueno
        self.empresa.save()
        self.producto = Producto.objects.create(empresa=self.empresa, codigo='BEB001', nombre='Coca Cola 2L',
                                                precio_unitario=Decimal('1.20'), pvp=Decimal('1.80'), stock=50)
        self.client.force_login(self.dueno)
        self.cobrar(2)                          # venta original de la demo
        guardar_foto('demo_comercio')

    def cobrar(self, cantidad):
        return self.client.post(reverse('empresa:crear_venta_multiple'), data=json.dumps({
            'productos': [{'id': self.producto.id, 'cantidad': cantidad, 'precio': '1.80'}],
            'tipo_pago': 'contado', 'monto_recibido': '50',
        }), content_type='application/json').json()

    def estado(self):
        empresa = User.objects.get(username='demo_comercio').empresa
        producto = Producto.objects.get(empresa=empresa, codigo='BEB001')
        return {
            'empresa': empresa.nombre,
            'ventas': Venta.objects.filter(empresa=empresa).count(),
            'productos': Producto.objects.filter(empresa=empresa).count(),
            'usuarios': User.objects.filter(empresa=empresa).count(),
            'coca': (producto.nombre, producto.pvp, producto.stock),
        }

    def actuar_como_visitante(self):
        self.cobrar(3)
        Producto.objects.create(empresa=self.empresa, codigo='VIS-1', nombre='Del visitante', precio_unitario=Decimal('1'))
        Producto.objects.filter(codigo='BEB001').update(nombre='Editado por visitante', pvp=Decimal('99'))
        Empresa.objects.filter(pk=self.empresa.pk).update(nombre='Renombrada por visitante')
        self.client.post(reverse('empresa:crear_empleado'), {
            'username': 'empleado_visitante', 'email': 'v@x.ec', 'first_name': 'V', 'last_name': 'X',
            'password1': 'Clave-segura-99', 'password2': 'Clave-segura-99', 'rol': 'vendedor',
        })
        venta_original = Venta.objects.filter(empresa=self.empresa).order_by('id').first()
        self.client.post(reverse('empresa:eliminar_venta', args=[venta_original.id]))

    def test_restaurar_revierte_lo_creado_editado_y_borrado(self):
        original = self.estado()
        self.actuar_como_visitante()
        self.assertNotEqual(self.estado(), original)
        self.assertTrue(User.objects.filter(username='empleado_visitante').exists())

        self.assertTrue(restaurar('demo_comercio'))

        self.assertEqual(self.estado(), original)
        self.assertFalse(User.objects.filter(username='empleado_visitante').exists())
        self.assertFalse(PoderEmpleado.objects.exists())
        # El dueño sigue pudiendo entrar con la misma cuenta
        self.assertTrue(self.client.login(username='demo_comercio', password='x'))

    def test_solo_restaura_si_pasaron_24_horas(self):
        self.actuar_como_visitante()
        self.assertFalse(restaurar_si_vencida('demo_comercio'))         # recién tomada
        DemoSnapshot.objects.update(ultimo_reset=timezone.now() - timedelta(hours=25))
        self.assertTrue(restaurar_si_vencida('demo_comercio'))
        self.assertEqual(self.estado()['empresa'], 'Minimarket Demo')

    def test_entrar_a_la_demo_restaura_si_esta_vencida(self):
        self.actuar_como_visitante()
        DemoSnapshot.objects.update(ultimo_reset=timezone.now() - timedelta(hours=25))
        self.client.logout()
        resp = self.client.get(reverse('empresa:acceso_rapido_demo', args=['demo_comercio']))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.estado()['empresa'], 'Minimarket Demo')
        self.assertFalse(User.objects.filter(username='empleado_visitante').exists())
