"""Huella estructural de cada pantalla, para comprobar que un rediseño visual no rompe nada.

Guarda por URL: ids, names de campos, atributos data-*, formularios (método, acción y
campos), modales, funciones llamadas por onclick y filas de cada tabla.

Uso:
    python scripts/qa_estructura.py guardar  qa/estructura_antes.json
    python scripts/qa_estructura.py comparar qa/estructura_antes.json
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import logging  # noqa: E402
import warnings  # noqa: E402

warnings.filterwarnings('ignore')
import django  # noqa: E402

django.setup()
logging.disable(logging.CRITICAL)

from django.conf import settings  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import URLPattern, URLResolver, get_resolver  # noqa: E402

settings.ALLOWED_HOSTS = ['*']
EXCLUIR = ('logout', 'webhook', 'reset', 'eliminar', 'delete', 'borrar', 'limpiar', 'pago/',
           'exportar', 'descargar', 'pdf', 'excel', 'api/', 'ejecutar', 'actualizar', 'validar')
CON_PARAMETRO = ['venta/{venta}/editar/', 'compra/{compra}/editar/', 'gasto/{gasto}/editar/',
                 'producto/{producto}/editar/']


class Huella(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.names, self.data_attrs, self.modales, self.onclicks = set(), set(), set(), set(), set()
        self.forms, self.tablas = [], []
        self._form = None
        self._tabla = None
        self._en_tbody = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
            if 'modal' in (a.get('class') or ''):
                self.modales.add(a['id'])
        if a.get('name') and tag in ('input', 'select', 'textarea', 'button'):
            self.names.add(a['name'])
            if self._form is not None:
                self._form['campos'].append(a['name'])
        for k in a:
            if k.startswith('data-') and not k.startswith('data-bs-'):
                self.data_attrs.add(k)
        if a.get('onclick'):
            m = re.match(r'\s*(?:return\s+)?([A-Za-z_$][\w$.]*)\s*\(', a['onclick'])
            if m:
                self.onclicks.add(m.group(1))
        if tag == 'form':
            self._form = {'metodo': (a.get('method') or 'get').lower(), 'accion': a.get('action') or '', 'campos': []}
        elif tag == 'table':
            self._tabla = {'id': a.get('id') or '', 'filas': 0}
        elif tag == 'tbody':
            self._en_tbody = True
        elif tag == 'tr' and self._en_tbody and self._tabla is not None:
            self._tabla['filas'] += 1

    def handle_endtag(self, tag):
        if tag == 'form' and self._form is not None:
            self._form['campos'] = sorted(set(self._form['campos']))
            self.forms.append(self._form)
            self._form = None
        elif tag == 'tbody':
            self._en_tbody = False
        elif tag == 'table' and self._tabla is not None:
            self.tablas.append(self._tabla)
            self._tabla = None

    def resultado(self):
        return {'ids': sorted(self.ids), 'names': sorted(self.names), 'data': sorted(self.data_attrs),
                'modales': sorted(self.modales), 'onclick': sorted(self.onclicks),
                'forms': self.forms, 'tablas': self.tablas}


def rutas():
    def recorrer(patrones, prefijo=''):
        for p in patrones:
            if isinstance(p, URLResolver):
                yield from recorrer(p.url_patterns, prefijo + str(p.pattern))
            elif isinstance(p, URLPattern):
                r = '/' + prefijo + str(p.pattern)
                if '<' not in r and '^' not in r:
                    yield r
    todas = sorted({r for r in recorrer(get_resolver().url_patterns) if r.startswith('/app-beta-2024/')})
    return [r for r in todas if not any(x in r for x in EXCLUIR)]


def capturar():
    from empresa.models import Compra, Gasto, Producto, Usuario, Venta
    usuario = Usuario.objects.get(username='demo_comercio')
    e = usuario.empresa
    ids = {'venta': Venta.objects.filter(empresa=e).order_by('id').first().id,
           'compra': Compra.objects.filter(empresa=e).order_by('id').first().id,
           'gasto': Gasto.objects.filter(empresa=e).order_by('id').first().id,
           'producto': Producto.objects.filter(empresa=e).order_by('id').first().id}
    urls = rutas() + ['/app-beta-2024/' + p.format(**ids) for p in CON_PARAMETRO]
    huellas = {}
    for url in urls:
        c = Client()
        c.force_login(usuario)
        r = c.get(url)
        if r.status_code != 200 or 'html' not in r.get('Content-Type', ''):
            huellas[url] = {'estado': r.status_code, 'tipo': r.get('Content-Type', '')}
            continue
        h = Huella()
        h.feed(r.content.decode('utf-8', 'ignore'))
        huellas[url] = dict(h.resultado(), estado=200)
    # Las rutas se guardan sin los ids concretos para poder comparar tras restaurar demos.
    return huellas


def comparar(antes, despues):
    problemas = []
    for url, a in antes.items():
        d = despues.get(url)
        if d is None:
            problemas.append(f'{url}: ya no se recorrió')
            continue
        if a.get('estado') != d.get('estado'):
            problemas.append(f"{url}: estado {a.get('estado')} -> {d.get('estado')}")
            continue
        if a.get('estado') != 200 or 'ids' not in a:
            continue
        for clave in ('ids', 'names', 'data', 'modales', 'onclick'):
            faltan = set(a[clave]) - set(d[clave])
            if faltan:
                problemas.append(f'{url}: faltan {clave}: {sorted(faltan)}')
        firma = lambda f: (f['metodo'], f['accion'], tuple(f['campos']))  # noqa: E731
        faltan_forms = {firma(f) for f in a['forms']} - {firma(f) for f in d['forms']}
        for f in faltan_forms:
            problemas.append(f'{url}: formulario cambiado {f}')
        filas_a = [t['filas'] for t in a['tablas']]
        filas_d = [t['filas'] for t in d['tablas']]
        if sorted(filas_a) != sorted(filas_d):
            problemas.append(f'{url}: filas de tablas {filas_a} -> {filas_d}')
    return problemas


if __name__ == '__main__':
    accion, archivo = sys.argv[1], sys.argv[2]
    if accion == 'guardar':
        os.makedirs(os.path.dirname(archivo) or '.', exist_ok=True)
        datos = capturar()
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)
        print(f'{len(datos)} pantallas guardadas en {archivo}')
    else:
        with open(archivo, encoding='utf-8') as f:
            antes = json.load(f)
        problemas = comparar(antes, capturar())
        print('\n'.join(problemas) if problemas else 'Sin diferencias estructurales.')
        print(f'{len(antes)} pantallas comparadas, {len(problemas)} diferencias')
        sys.exit(1 if problemas else 0)
