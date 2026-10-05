"""Test de humo: ninguna página sin parámetros debe responder con error 500.

Recorre todas las rutas del namespace `empresa` que no reciben argumentos,
con una empresa que tiene ventas, compras, gastos y capital, y falla si alguna
lanza una excepción o devuelve 5xx.

RUTAS_CON_DEUDA documenta las páginas rotas conocidas que aún no están en el
menú. Al arreglar una, quítala de la lista: el test empezará a protegerla.
"""
import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver

from empresa.models import Compra, Empresa, Gasto, Producto, Venta

User = get_user_model()

# Rutas que no se prueban porque modifican datos o dependen de servicios externos.
# Las rutas de IA sí se prueban: sin clave en tests usan el análisis local (sin red).
EXCLUIR = ('logout', 'webhook', 'reset', 'eliminar', 'delete', 'borrar', 'limpiar',
           'pago/', 'ejecutar', 'actualizar')

RUTAS_CON_DEUDA = set()


def _rutas_sin_parametros():
    def recorrer(patrones, prefijo=''):
        for p in patrones:
            if isinstance(p, URLResolver):
                yield from recorrer(p.url_patterns, prefijo + str(p.pattern))
            elif isinstance(p, URLPattern):
                ruta = '/' + prefijo + str(p.pattern)
                if '<' not in ruta and '(?P' not in ruta and '^' not in ruta:
                    yield ruta
    return sorted({r for r in recorrer(get_resolver().url_patterns) if r.startswith('/app-beta-2024/')})


class SmokeRutasTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre="Tienda Smoke", ruc="1792146739001", direccion="Quito", categoria="comercio"
        )
        self.user = User.objects.create_user(username="dueno_smoke", password="x", empresa=self.empresa)
        self.empresa.propietario = self.user
        self.empresa.save()
        producto = Producto.objects.create(
            empresa=self.empresa, codigo="SMK001", nombre="Producto Smoke",
            precio_unitario=Decimal('1.00'), pvp=Decimal('1.50'), stock=50, stock_minimo=5,
        )
        Compra.objects.create(empresa=self.empresa, producto=producto, cantidad=10,
                              monto_neto=Decimal('10.00'), iva=Decimal('1.50'), monto=Decimal('11.50'),
                              tasa_iva=Decimal('15'))
        Venta.objects.create(empresa=self.empresa, producto=producto, cantidad=2,
                             precio_unitario=Decimal('1.50'), monto_neto=Decimal('3.00'),
                             monto=Decimal('0'), tasa_iva=Decimal('15'))
        Gasto.objects.create(empresa=self.empresa, descripcion="Luz", monto=Decimal('5.00'))
        self.client.force_login(self.user)
        self.client.post('/app-beta-2024/capital/registrar/',
                         {'tipo': 'aporte', 'monto': '100', 'descripcion': 'Capital inicial'})

    def test_ninguna_ruta_devuelve_500(self):
        fallos = []
        for ruta in _rutas_sin_parametros():
            if ruta in RUTAS_CON_DEUDA or any(x in ruta for x in EXCLUIR):
                continue
            try:
                resp = self.client.get(ruta)
                if resp.status_code >= 500:
                    fallos.append(f'{ruta} -> {resp.status_code}')
            except Exception as e:  # noqa: BLE001 - queremos reportar cualquier excepción
                fallos.append(f'{ruta} -> {type(e).__name__}: {str(e)[:120]}')
        self.assertEqual(fallos, [], 'Rutas con error:\n' + '\n'.join(fallos))

    def test_rutas_con_deuda_siguen_rotas(self):
        """Avisa cuando una ruta de la lista de deuda ya funciona, para quitarla de la lista."""
        arregladas = []
        for ruta in sorted(RUTAS_CON_DEUDA):
            try:
                if self.client.get(ruta).status_code < 500:
                    arregladas.append(ruta)
            except Exception:
                pass
        self.assertEqual(arregladas, [], 'Ya funcionan; quítalas de RUTAS_CON_DEUDA: ' + json.dumps(arregladas))
