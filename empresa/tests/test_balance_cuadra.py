"""El Balance debe cuadrar (Activo = Pasivo + Patrimonio) tras operaciones típicas."""
import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from empresa.models import Compra, Empresa, Gasto, Producto
from empresa.services.reportes_niif_service import ReportesNIIFService

User = get_user_model()


class BalanceCuadraTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Tienda', ruc='1792146739001', direccion='Quito', categoria='comercial')
        self.user = User.objects.create_user(username='duena', password='x', empresa=self.empresa)
        self.empresa.propietario = self.user
        self.empresa.save()
        self.client.force_login(self.user)

        # Aporte inicial por la pantalla de Capital (genera su asiento)
        self.client.post(reverse('empresa:registrar_capital'), {'tipo': 'aporte', 'monto': '1000', 'descripcion': 'Capital inicial'})
        self.producto = Producto.objects.create(empresa=self.empresa, codigo='P1', nombre='Agua',
                                                precio_unitario=Decimal('0.30'), pvp=Decimal('0.50'), stock=0)
        Compra.objects.create(empresa=self.empresa, producto=self.producto, cantidad=100,
                              monto_neto=Decimal('30.00'), iva=Decimal('4.50'), monto=Decimal('34.50'),
                              tasa_iva=Decimal('15'))
        self.producto.refresh_from_db()
        self.client.post(reverse('empresa:crear_venta_multiple'), data=json.dumps({
            'productos': [{'id': self.producto.id, 'cantidad': 10, 'precio': '0.50'}],
            'tipo_pago': 'contado', 'monto_recibido': '10', 'incluir_iva': True,
        }), content_type='application/json')
        Gasto.objects.create(empresa=self.empresa, descripcion='Luz', monto=Decimal('2.00'))

    def _totales_vista(self):
        ctx = self.client.get(reverse('empresa:balance_general')).context
        datos = {}
        for capa in ctx:
            datos.update(capa.flatten())
        return float(datos['total_activos']), float(datos['total_pasivos']) + float(datos['total_patrimonio'])

    def test_balance_niif_cuadra(self):
        totales = ReportesNIIFService.generar_estado_situacion_financiera(self.empresa)['totales']
        self.assertTrue(totales['cuadra'], totales)
        self.assertIn('Resultado del ejercicio',
                      ReportesNIIFService.generar_estado_situacion_financiera(self.empresa)['patrimonio'])

    def test_balance_general_coincide_con_niif(self):
        activos, pasivo_mas_patrimonio = self._totales_vista()
        self.assertAlmostEqual(activos, pasivo_mas_patrimonio, places=2)
        niif = ReportesNIIFService.generar_estado_situacion_financiera(self.empresa)['totales']
        # El aporte no se cuenta dos veces: ambos reportes muestran el mismo activo total.
        self.assertAlmostEqual(activos, niif['total_activos'], places=2)
