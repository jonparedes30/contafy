"""Escáner de productos: lectura de códigos, identificación por foto y errores."""
import json
from decimal import Decimal
from unittest import mock

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from empresa.models import Empresa, Producto
from empresa.services import escaner_service as esc

User = get_user_model()
CLAVE_FALSA = 'AIzaFAKE-clave-que-no-debe-filtrarse'


def respuesta_vision(logos=(), texto=''):
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {'responses': [{
        'logoAnnotations': [{'description': l} for l in logos],
        'fullTextAnnotation': {'text': texto} if texto else {},
        'labelAnnotations': [{'description': 'Bottle'}],
    }]}
    return resp


class CodigosTests(TestCase):
    def test_valida_digito_verificador(self):
        self.assertTrue(esc.codigo_gtin_valido('7861900001381'))   # EAN-13
        self.assertTrue(esc.codigo_gtin_valido('96385074'))        # EAN-8
        self.assertFalse(esc.codigo_gtin_valido('7861900001382'))  # verificador incorrecto
        self.assertFalse(esc.codigo_gtin_valido('0912345678'))     # 10 dígitos (registro sanitario)

    def test_ignora_lotes_y_registros(self):
        texto = 'Reg. San. 0912345678\nLote 20260512\n7861900001381'
        self.assertEqual(esc.extraer_codigos(texto), ['7861900001381'])

    def test_normaliza_marcas(self):
        self.assertEqual(esc.normalizar('Coca-Cola®'), 'coca cola')
        self.assertEqual(esc.normalizar('LÁCTEOS'), 'lacteos')


@override_settings(GOOGLE_VISION_API_KEY=CLAVE_FALSA)
class IdentificarTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Mini', ruc='1792146739001', direccion='Quito', categoria='comercial')
        crear = lambda codigo, nombre, stock, barras='': Producto.objects.create(
            empresa=self.empresa, codigo=codigo, nombre=nombre, codigo_barras=barras or None,
            precio_unitario=Decimal('1'), pvp=Decimal('1.5'), stock=stock)
        self.coca = crear('BEB001', 'Coca Cola 2L', 10, '7861900001381')
        self.doritos = crear('SNK001', 'Doritos Nacho', 10)
        self.chochos = crear('SNK002', 'Chochos Salados', 10)
        self.yogurt = crear('LAC002', 'Yogurt Toni 1L', 0)

    def identificar_foto(self, logos=(), texto='', contexto='compra'):
        with mock.patch.object(esc.requests, 'post', return_value=respuesta_vision(logos, texto)):
            return esc.identificar(self.empresa, contexto=contexto, imagen_b64='abc')

    def nombres(self, r):
        return [p['nombre'] for p in r['productos']]

    def test_codigo_leido_por_camara(self):
        r = esc.identificar(self.empresa, contexto='venta', codigo='7861900001381')
        self.assertEqual(self.nombres(r), ['Coca Cola 2L'])
        self.assertEqual(r['origen'], 'codigo')

    def test_codigo_interno_sin_distinguir_mayusculas(self):
        self.assertEqual(self.nombres(esc.identificar(self.empresa, codigo='snk001')), ['Doritos Nacho'])

    def test_foto_coca_cola_con_logo_con_guion(self):
        r = self.identificar_foto(logos=['Coca-Cola'], texto='Coca-Cola\nSabor Original\n2 L')
        self.assertEqual(self.nombres(r)[0], 'Coca Cola 2L')

    def test_foto_texto_con_letras_l_y_g(self):
        # Antes se descartaba toda línea con "l" o "g" por el filtro de ruido.
        r = self.identificar_foto(texto='CHOCHOS SALADOS\nLote 20260512\nPeso neto 200 g')
        self.assertEqual(self.nombres(r)[0], 'Chochos Salados')

    def test_foto_usa_codigo_valido_y_no_el_registro_sanitario(self):
        r = self.identificar_foto(texto='Reg. San. 0912345678\n7861900001381')
        self.assertEqual(r['codigo_detectado'], '7861900001381')
        self.assertEqual(self.nombres(r), ['Coca Cola 2L'])

    def test_producto_inexistente(self):
        r = self.identificar_foto(logos=['Pepsi'], texto='PEPSI\n2 L')
        self.assertFalse(r['found'])
        self.assertTrue(r['mensaje'])

    def test_venta_sin_stock_explica_el_motivo(self):
        r = esc.identificar(self.empresa, contexto='venta', codigo='LAC002')
        self.assertFalse(r['found'])
        self.assertIn('no tiene stock', r['mensaje'])

    def test_error_de_google_no_expone_la_clave(self):
        error = requests.exceptions.HTTPError(
            f'400 Client Error for url: https://vision.googleapis.com/v1/images:annotate?key={CLAVE_FALSA}')
        with mock.patch.object(esc.requests, 'post', side_effect=error):
            with self.assertRaises(esc.EscanerError) as ctx:
                esc.identificar(self.empresa, imagen_b64='abc')
        self.assertNotIn(CLAVE_FALSA, str(ctx.exception))

    @override_settings(GOOGLE_VISION_API_KEY='')
    def test_sin_clave_mensaje_para_el_usuario(self):
        with self.assertRaises(esc.EscanerError) as ctx:
            esc.identificar(self.empresa, imagen_b64='abc')
        self.assertNotIn('settings', str(ctx.exception))


class VistaEscanerTests(TestCase):
    def setUp(self):
        empresa = Empresa.objects.create(nombre='Mini', ruc='1792146739001', direccion='Quito', categoria='comercial')
        user = User.objects.create_user(username='cajero', password='x', empresa=empresa)
        Producto.objects.create(empresa=empresa, codigo='BEB001', nombre='Coca Cola 2L', codigo_barras='7861900001381',
                                precio_unitario=Decimal('1.20'), pvp=Decimal('1.80'), stock=5)
        self.client.force_login(user)

    def test_vista_con_codigo(self):
        resp = self.client.post(reverse('empresa:vision_search_api'),
                                data=json.dumps({'codigo': '7861900001381', 'contexto': 'venta'}),
                                content_type='application/json')
        data = resp.json()
        self.assertTrue(data['found'])
        self.assertEqual(data['productos'][0]['precio_venta'], 1.80)
