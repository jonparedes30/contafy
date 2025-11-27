class ResumenPresenter:
    """Normaliza y expone un contexto estable para las plantillas de resumen.

    Recibe la empresa (opcional) y un diccionario con datos calculados
    por la vista. Devuelve un contexto con tipos y defaults seguros.
    """
    def __init__(self, empresa=None, data=None):
        self.empresa = empresa
        self.data = data or {}

    def _num(self, key, default=0.0):
        try:
            return float(self.data.get(key, default) or default)
        except Exception:
            return float(default)

    def _list(self, key):
        v = self.data.get(key)
        return v if isinstance(v, (list, tuple)) else []

    def _dict(self, key):
        v = self.data.get(key)
        return v if isinstance(v, dict) else {}

    def to_context(self):
        ventas = self._num('ventas')
        compras = self._num('compras')
        gastos = self._num('gastos')
        utilidad_bruta = self._num('utilidad_bruta')
        utilidad_neta = self._num('utilidad_neta')

        margen_neto = round((utilidad_neta / ventas * 100) if ventas > 0 else 0, 2)
        margen_bruto = round((utilidad_bruta / ventas * 100) if ventas > 0 else 0, 2)
        ratio_gastos_ventas = round((gastos / ventas * 100) if ventas > 0 else 0, 2)
        ratio_costos = round((compras / ventas * 100) if ventas > 0 else 0, 2)

        context = {
            'ventas': ventas,
            'compras': compras,
            'gastos': gastos,
            'utilidad_bruta': utilidad_bruta,
            'utilidad_neta': utilidad_neta,
            'productos_vendidos': self._list('productos_vendidos'),
            'gastos_por_categoria': self._list('gastos_por_categoria'),
            'recomendaciones': self._list('recomendaciones'),
            'conclusion': self._dict('conclusion'),
            'margen_neto': margen_neto,
            'margen_bruto': margen_bruto,
            'ratio_gastos_ventas': ratio_gastos_ventas,
            'ratio_costos': ratio_costos,
            'analisis_predictivo': self._dict('analisis_predictivo'),
        }

        # Exponer también una lista de KPI homogénea para incluir en templates
        context['kpis'] = [
            {'label': 'Total Ventas', 'value': ventas, 'type': 'neutro'},
            {'label': 'Total Compras', 'value': compras, 'type': 'costo'},
            {'label': 'Total Gastos', 'value': gastos, 'type': 'gasto'},
            {'label': 'Utilidad Neta', 'value': utilidad_neta, 'type': 'utilidad', 'positive': utilidad_neta >= 0},
        ]

        # Añadir business_type si está disponible
        context['business_type'] = getattr(self.empresa, 'categoria', 'default') if self.empresa else 'default'

        return context
