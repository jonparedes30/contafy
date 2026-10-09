"""Escáner v2: motivo sin resultado, catálogo público, verificación de código y registro rápido."""
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from empresa.models import Empresa, Producto
from empresa.services import escaner_service as esc

User = get_user_model()


def respuesta_catalogo(datos, estado=200):
    resp = mock.Mock(status_code=estado)
    resp.json.return_value = datos
    return resp


class MotivoYCatalogoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.empresa = Empresa.objects.create(nombre='Mini', ruc='1792146739001', direccion='Quito', categoria='comercial')
        Producto.objects.create(empresa=self.empresa, codigo='LAC002', nombre='Yogurt', codigo_barras='7861900001381',
                                precio_unitario=Decimal('1'), pvp=Decimal('1.5'), stock=0)

    def test_motivo_no_existe_y_sin_stock(self):
        self.assertEqual(esc.identificar(self.empresa, contexto='venta', codigo='0000000000017')['motivo'], 'no_existe')
        r = esc.identificar(self.empresa, contexto='venta', codigo='7861900001381')
        self.assertEqual(r['motivo'], 'sin_stock')
        self.assertEqual(r['producto_sin_stock']['nombre'], 'Yogurt')

    def test_catalogo_sugiere_nombre_con_presentacion(self):
        datos = {'status': 1, 'product': {'product_name': 'Coca-Cola Original', 'brands': 'COCA-COLA SERVICES SA/NV',
                                          'quantity': '330 ml', 'categories': 'Bebidas, en:sodas, Colas'}}
        with mock.patch.object(esc.requests, 'get', return_value=respuesta_catalogo(datos)) as get:
            s = esc.buscar_en_catalogo_publico('5449000000996')
            esc.buscar_en_catalogo_publico('5449000000996')  # segunda vez: desde caché
        self.assertEqual(s['nombre'], 'Coca-Cola Original 330 ml')
        self.assertEqual(s['categoria'], 'Colas')
        self.assertEqual(get.call_count, 1)

    def test_catalogo_no_consulta_codigos_invalidos_ni_falla_sin_red(self):
        with mock.patch.object(esc.requests, 'get') as get:
            self.assertIsNone(esc.buscar_en_catalogo_publico('BEB001'))
            get.assert_not_called()
        with mock.patch.object(esc.requests, 'get', side_effect=esc.requests.exceptions.Timeout):
            self.assertIsNone(esc.buscar_en_catalogo_publico('5449000000996'))

    @override_settings(CATALOGO_PUBLICO_ACTIVO=False)
    def test_catalogo_desactivado(self):
        with mock.patch.object(esc.requests, 'get') as get:
            self.assertIsNone(esc.buscar_en_catalogo_publico('5449000000996'))
            get.assert_not_called()


class RegistroRapidoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.empresa = Empresa.objects.create(nombre='Mini', ruc='1792146739001', direccion='Quito', categoria='comercial')
        self.user = User.objects.create_user(username='duena', password='x', empresa=self.empresa)
        self.empresa.propietario = self.user
        self.empresa.save()
        self.coca = Producto.objects.create(empresa=self.empresa, codigo='BEB001', nombre='Coca Cola 2L',
                                            codigo_barras='7861900001381', precio_unitario=Decimal('1.2'),
                                            pvp=Decimal('1.8'), stock=5)
        self.client.force_login(self.user)

    def test_verificar_codigo_existente_y_en_edicion(self):
        url = reverse('empresa:producto_info_api')
        data = self.client.get(url, {'codigo': '7861900001381'}).json()
        self.assertTrue(data['encontrado'])
        self.assertIn(f'/producto/{self.coca.id}/editar/', data['url_editar'])
        data = self.client.get(url, {'codigo': '7861900001381', 'excluir': self.coca.id}).json()
        self.assertFalse(data['encontrado'])
        self.assertNotIn('traceback', data)

    def test_registro_embebido_devuelve_producto_y_permite_marco(self):
        resp = self.client.post(reverse('empresa:crear_producto'), {
            'embebido': '1', 'codigo': '', 'codigo_barras': '7861068700171', 'nombre': 'Galleta local',
            'precio_unitario': '0.50', 'pvp': '1.00', 'stock': '4', 'stock_minimo': '0', 'stock_maximo': '0',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'empresa/producto_guardado_embebido.html')
        self.assertEqual(resp.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        producto = Producto.objects.get(codigo_barras='7861068700171')
        self.assertEqual(producto.codigo, 'P-0002')  # código interno automático
        self.assertContains(resp, 'contafy:producto-guardado')

    def test_registro_normal_sigue_redirigiendo(self):
        resp = self.client.post(reverse('empresa:crear_producto'), {
            'codigo': 'X1', 'nombre': 'Normal', 'precio_unitario': '1', 'pvp': '2', 'stock': '0',
            'stock_minimo': '0', 'stock_maximo': '0',
        })
        self.assertEqual(resp.status_code, 302)
