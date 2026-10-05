"""El código de producto es único por empresa, no en todo el sistema."""
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from empresa.forms import ProductoForm
from empresa.models import Empresa, Producto


class CodigoProductoPorEmpresaTests(TestCase):
    def setUp(self):
        self.a = Empresa.objects.create(nombre='A', ruc='1792146739001', direccion='x', categoria='comercial')
        self.b = Empresa.objects.create(nombre='B', ruc='1710034065001', direccion='x', categoria='comercial')
        Producto.objects.create(empresa=self.a, codigo='P001', codigo_barras='7861900001381', nombre='Agua',
                                precio_unitario=Decimal('1'), stock=1)

    def datos(self, **extra):
        return dict({'codigo': 'P001', 'nombre': 'Otro', 'precio_unitario': '1', 'stock': '0', 'stock_minimo': '0'}, **extra)

    def test_otra_empresa_puede_usar_el_mismo_codigo(self):
        self.assertTrue(ProductoForm(self.datos(codigo_barras='7861900001381'), empresa=self.b).is_valid())

    def test_misma_empresa_no_repite_codigo_ni_codigo_de_barras(self):
        form = ProductoForm(self.datos(codigo='p001'), empresa=self.a)
        self.assertFalse(form.is_valid())
        self.assertIn('codigo', form.errors)
        form = ProductoForm(self.datos(codigo='P002', codigo_barras='7861900001381'), empresa=self.a)
        self.assertIn('codigo_barras', form.errors)

    def test_restriccion_en_base_de_datos(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Producto.objects.create(empresa=self.a, codigo='P001', nombre='Duplicado', precio_unitario=Decimal('1'))
        # Varios productos sin código de barras no chocan entre sí.
        Producto.objects.create(empresa=self.a, codigo='P010', nombre='Sin código 1', precio_unitario=Decimal('1'))
        Producto.objects.create(empresa=self.a, codigo='P011', nombre='Sin código 2', precio_unitario=Decimal('1'))
