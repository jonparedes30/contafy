"""Ciclo completo: registro -> login -> alta de trabajador -> operaciones con su autoría."""
import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from empresa.models import (
    CodigoInvitacion, MovimientoContable, PoderEmpleado, Producto, RegistroAuditoria, Venta,
)

User = get_user_model()

DATOS_REGISTRO = {
    'modo_demo': '0',
    'codigo_invitacion': 'CONTAFY-PRUEBA1',
    'first_name': 'Ana', 'last_name': 'Torres', 'email': 'ana@tienda.ec', 'username': 'ana_torres',
    'password1': 'Clave-segura-2026', 'password2': 'Clave-segura-2026',
    'nombre_empresa': 'Tienda Ana', 'ruc': '1792146739001', 'direccion': 'Av. Amazonas N24',
    'categoria': 'comercial', 'tipo_negocio': 'Minimarket',
    'provincia': 'pichincha', 'ciudad': 'Quito', 'telefono_whatsapp': '0987654321',
    'latitud': '-0.1806532', 'longitud': '-78.4678382',
}


class FlujoUsuariosTests(TestCase):
    def setUp(self):
        CodigoInvitacion.objects.create(codigo='CONTAFY-PRUEBA1')

    def registrar(self, **cambios):
        return self.client.post(reverse('empresa:registro'), dict(DATOS_REGISTRO, **cambios))

    # ---------- Registro ----------
    def test_registro_crea_usuario_empresa_y_consume_el_codigo(self):
        resp = self.registrar()
        self.assertRedirects(resp, reverse('empresa:login'), fetch_redirect_response=False)

        user = User.objects.get(username='ana_torres')
        empresa = user.empresa
        self.assertEqual((user.first_name, user.last_name, user.email), ('Ana', 'Torres', 'ana@tienda.ec'))
        self.assertEqual(empresa.propietario, user)
        self.assertEqual((empresa.nombre, empresa.ruc, empresa.categoria, empresa.tipo_negocio),
                         ('Tienda Ana', '1792146739001', 'comercial', 'Minimarket'))
        self.assertEqual((empresa.provincia, empresa.ciudad), ('pichincha', 'Quito'))
        self.assertEqual(empresa.telefono_whatsapp, '+593987654321')
        self.assertIsNotNone(empresa.latitud)
        self.assertFalse(empresa.es_demo)
        codigo = CodigoInvitacion.objects.get(codigo='CONTAFY-PRUEBA1')
        self.assertTrue(codigo.usado)
        self.assertEqual(codigo.usado_por, user)

    def test_codigo_invalido_conserva_lo_escrito(self):
        resp = self.registrar(codigo_invitacion='NO-EXISTE')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='ana_torres').exists())
        self.assertContains(resp, 'El código no es válido')
        self.assertContains(resp, 'value="Tienda Ana"')   # no se pierde lo escrito

    def test_registro_demo_marca_la_empresa(self):
        resp = self.registrar(modo_demo='1', codigo_invitacion='')
        self.assertEqual(resp.status_code, 302)
        empresa = User.objects.get(username='ana_torres').empresa
        self.assertTrue(empresa.es_demo)
        self.assertIsNotNone(empresa.demo_expira)

    def test_validacion_por_etapa(self):
        User.objects.create_user(username='ocupado', password='x')
        resp = self.client.post(reverse('empresa:registro_validar'), {
            'campos': ['username', 'email', 'ruc', 'password2', 'codigo_invitacion'],
            'username': 'ocupado', 'email': 'malo', 'ruc': '1234567890123',
            'password1': 'Clave-segura-2026', 'password2': 'otra', 'codigo_invitacion': 'NO-EXISTE',
        })
        errores = resp.json()['errores']
        self.assertEqual(set(errores), {'username', 'email', 'ruc', 'password2', 'codigo_invitacion'})

    # ---------- Login ----------
    def test_login_y_bloqueo_de_credenciales_erroneas(self):
        self.registrar()
        malo = self.client.post(reverse('empresa:login'), {'username': 'ana_torres', 'password': 'equivocada'})
        self.assertEqual(malo.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

        bueno = self.client.post(reverse('empresa:login'), {'username': 'ana_torres', 'password': 'Clave-segura-2026'})
        self.assertEqual(bueno.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), User.objects.get(username='ana_torres').id)

    # ---------- Trabajadores y operaciones ----------
    def test_trabajador_con_rol_registra_venta_con_su_autoria(self):
        self.registrar()
        duena = User.objects.get(username='ana_torres')
        empresa = duena.empresa
        producto = Producto.objects.create(empresa=empresa, codigo='P1', nombre='Agua', codigo_barras='7861900001381',
                                           precio_unitario=Decimal('0.30'), pvp=Decimal('0.50'), stock=50)
        self.client.force_login(duena)

        # La dueña crea un cajero con el rol "vendedor"
        resp = self.client.post(reverse('empresa:crear_empleado'), {
            'username': 'cajero1', 'email': 'cajero@tienda.ec', 'first_name': 'Luis', 'last_name': 'Mora',
            'password1': 'Cajero-seguro-77', 'password2': 'Cajero-seguro-77', 'rol': 'vendedor',
        })
        self.assertEqual(resp.status_code, 302)
        cajero = User.objects.get(username='cajero1')
        self.assertEqual(cajero.empresa, empresa)
        poderes = PoderEmpleado.objects.get(empleado=cajero, empresa=empresa)
        self.assertTrue(poderes.puede_registrar_ventas)
        self.assertFalse(poderes.puede_gestionar_cuentas)

        # El cajero entra con su propia contraseña y cobra una venta
        self.client.logout()
        self.assertEqual(self.client.post(reverse('empresa:login'),
                                          {'username': 'cajero1', 'password': 'Cajero-seguro-77'}).status_code, 302)
        data = self.client.post(reverse('empresa:crear_venta_multiple'), data=json.dumps({
            'productos': [{'id': producto.id, 'cantidad': 2, 'precio': '0.50'}],
            'tipo_pago': 'contado', 'monto_recibido': '5',
        }), content_type='application/json').json()
        self.assertTrue(data['success'], data)

        venta = Venta.objects.get(id=data['ventas_ids'][0])
        self.assertEqual(venta.creado_por, cajero)
        self.assertEqual(venta.empresa, empresa)
        self.assertTrue(MovimientoContable.objects.filter(empresa=empresa, transaccion_id=venta.transaccion_id_contable).exists())
        auditoria = RegistroAuditoria.objects.filter(empresa=empresa, modelo='Venta', objeto_id=venta.id)
        self.assertTrue(auditoria.exists())
        self.assertEqual(auditoria.first().usuario, cajero)

        # Sin permiso de cuentas no puede registrar capital
        resp = self.client.post(reverse('empresa:registrar_capital'),
                                {'tipo': 'aporte', 'monto': '100', 'descripcion': 'x'})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(MovimientoContable.objects.filter(empresa=empresa, descripcion__startswith='Aporte').exists())

    def test_se_puede_borrar_una_empresa_con_ventas_y_trabajadores(self):
        # P. ej. al limpiar una cuenta demo vencida. Antes fallaba con IntegrityError:
        # la auditoría registraba cada eliminación de la cascada apuntando a la empresa borrada.
        self.test_trabajador_con_rol_registra_venta_con_su_autoria()
        empresa = User.objects.get(username='ana_torres').empresa
        empresa.delete()
        self.assertFalse(User.objects.filter(username__in=['ana_torres', 'cajero1']).exists())
        self.assertFalse(Venta.objects.filter(empresa_id=empresa.pk).exists())
        self.assertFalse(RegistroAuditoria.objects.filter(empresa_id=empresa.pk).exists())

    def test_no_se_borra_un_trabajador_que_registro_operaciones(self):
        # La autoría de las ventas no se pierde: borrar solo al usuario está restringido.
        from django.db.models.deletion import RestrictedError
        self.test_trabajador_con_rol_registra_venta_con_su_autoria()
        with self.assertRaises(RestrictedError):
            User.objects.get(username='cajero1').delete()
