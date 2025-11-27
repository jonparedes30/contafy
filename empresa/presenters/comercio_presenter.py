from django.db.models import F, Q, Sum

class ComercioPresenter:
    """Construye contexto seguro para vistas de comercio (retail/wholesale).
    
    Normaliza métricas específicas de negocios comerciales:
    - Inventario y rotación de productos
    - Márgenes de venta por categoría
    - Top productos por volumen y rentabilidad
    - Clientes más activos
    """
    def __init__(self, empresa):
        self.empresa = empresa

    def _num(self, value, default=0.0):
        try:
            return float(value or default)
        except Exception:
            return float(default)

    def to_context(self):
        from empresa.models import Producto, Venta, Cliente

        empresa = self.empresa

        # Totales de inventario
        total_productos = Producto.objects.filter(
            empresa=empresa,
            activo=True
        ).count()
        
        # Productos con stock bajo (stock <= stock_minimo)
        productos_stock_bajo = list(
            Producto.objects.filter(
                empresa=empresa,
                stock__lte=F('stock_minimo'),
                activo=True
            )[:10]
        )

        # Top 5 productos por volumen de ventas (cantidad)
        top_productos_volumen = list(
            Venta.objects.filter(
                empresa=empresa
            ).values('producto__nombre', 'producto__codigo')
            .annotate(total_cantidad=Sum('cantidad'))
            .order_by('-total_cantidad')[:5]
        )

        # Top 5 clientes por compras totales
        top_clientes = list(
            Venta.objects.filter(empresa=empresa)
            .values('cliente_fk__nombre', 'cliente_fk__ruc')
            .annotate(total_compras=Sum('monto'))
            .order_by('-total_compras')[:5]
        )

        # Métricas de margen (si hay ventas recientes)
        ventas_recientes = Venta.objects.filter(empresa=empresa).aggregate(
            total_ventas=Sum('monto'),
            total_costo=Sum('monto_neto')
        )
        
        total_ventas = self._num(ventas_recientes['total_ventas'])
        total_costo = self._num(ventas_recientes['total_costo'])
        margen_bruto = total_ventas - total_costo if total_ventas > 0 else 0
        margen_bruto_pct = round((margen_bruto / total_ventas * 100) if total_ventas > 0 else 0, 2)

        # Rotación de inventario (aproximado)
        rotacion_inventario = 0.0
        if total_costo > 0:
            # Sumar valor de inventario en stock
            inventario_total_valor = sum(
                self._num(p.precio_unitario or 0) * self._num(p.stock or 0)
                for p in Producto.objects.filter(empresa=empresa, stock__gt=0, activo=True)
            )
            if inventario_total_valor > 0:
                rotacion_inventario = round(total_costo / inventario_total_valor, 2)

        return {
            'total_productos': total_productos,
            'productos_stock_bajo': productos_stock_bajo,
            'top_productos_volumen': top_productos_volumen,
            'top_clientes': top_clientes,
            'total_ventas': total_ventas,
            'total_costo': total_costo,
            'margen_bruto': margen_bruto,
            'margen_bruto_pct': margen_bruto_pct,
            'rotacion_inventario': rotacion_inventario,
        }
