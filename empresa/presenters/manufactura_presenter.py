from django.db.models import F

class ManufacturaPresenter:
    """Construye contexto seguro para vistas de manufactura."""
    def __init__(self, empresa):
        self.empresa = empresa

    def to_context(self):
        # Importar modelos localmente para evitar overhead si no se usa
        from empresa.models import MateriaPrima, ProductoManufacturado, OrdenProduccion

        empresa = self.empresa

        total_materias_primas = MateriaPrima.objects.filter(empresa=empresa).count()
        total_productos = ProductoManufacturado.objects.filter(empresa=empresa, activo=True).count()
        ordenes_pendientes = OrdenProduccion.objects.filter(empresa=empresa, estado='pendiente').count()
        ordenes_en_proceso = OrdenProduccion.objects.filter(empresa=empresa, estado='en_proceso').count()

        materias_stock_bajo = list(MateriaPrima.objects.filter(empresa=empresa, stock_actual__lte=F('stock_minimo'))[:5])
        productos_stock_bajo = list(ProductoManufacturado.objects.filter(empresa=empresa, stock_actual__lte=F('stock_minimo'), activo=True)[:5])
        ordenes_recientes = list(OrdenProduccion.objects.filter(empresa=empresa).order_by('-creado_en')[:5])

        return {
            'total_materias_primas': total_materias_primas,
            'total_productos': total_productos,
            'ordenes_pendientes': ordenes_pendientes,
            'ordenes_en_proceso': ordenes_en_proceso,
            'materias_stock_bajo': materias_stock_bajo,
            'productos_stock_bajo': productos_stock_bajo,
            'ordenes_recientes': ordenes_recientes,
        }
