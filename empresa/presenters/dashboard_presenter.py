class DashboardPresenter:
    """Normaliza contexto para dashboard principal"""
    
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
        ventas_hoy = self._num('ventas_hoy')
        ventas_mes = self._num('ventas_mes')
        gastos_mes = self._num('gastos_mes')
        utilidad_mes = self._num('utilidad_mes')
        
        context = {
            'ventas_hoy': ventas_hoy,
            'ventas_mes': ventas_mes,
            'gastos_mes': gastos_mes,
            'utilidad_mes': utilidad_mes,
            'ventas_recientes': self._list('ventas_recientes'),
            'productos_stock_bajo': self._list('productos_stock_bajo'),
            'alertas': self._list('alertas'),
            'graficos': self._dict('graficos'),
        }
        
        # KPIs para dashboard
        context['kpis_dashboard'] = [
            {'label': 'Ventas Hoy', 'value': ventas_hoy, 'icon': 'currency-dollar', 'type': 'primary'},
            {'label': 'Ventas Mes', 'value': ventas_mes, 'icon': 'graph-up', 'type': 'success'},
            {'label': 'Gastos Mes', 'value': gastos_mes, 'icon': 'cash-stack', 'type': 'danger'},
            {'label': 'Utilidad Mes', 'value': utilidad_mes, 'icon': 'calculator', 'type': 'info'},
        ]
        
        context['business_type'] = getattr(self.empresa, 'categoria', 'default') if self.empresa else 'default'
        
        return context
