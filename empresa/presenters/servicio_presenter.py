from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

class ServicioPresenter:
    """Construye contexto seguro para vistas de servicios.
    
    Normaliza métricas específicas de negocios de servicios:
    - Ordenes de servicio pendientes y completadas
    - Clientes activos y satisfacción
    - Ingresos por tipo de servicio
    - Utilización de recursos
    """
    def __init__(self, empresa):
        self.empresa = empresa

    def _num(self, value, default=0.0):
        try:
            return float(value or default)
        except Exception:
            return float(default)

    def to_context(self):
        from empresa.models import Venta, Cliente

        empresa = self.empresa

        # Ordenes de servicio (mapear a Ventas)
        ordenes_totales = Venta.objects.filter(empresa=empresa).count()
        
        # Ordenes pendientes y completadas (asumimos que todas las ventas son "completadas" por defecto)
        ordenes_pendientes = 0
        ordenes_completadas = ordenes_totales

        # Clientes activos (con compras en últimos 30 días)
        hace_30 = timezone.now() - timedelta(days=30)
        clientes_activos = Venta.objects.filter(
            empresa=empresa,
            fecha__gte=hace_30
        ).values('cliente_fk').distinct().count()

        # Ingresos totales por servicio
        ingresos_totales = Venta.objects.filter(empresa=empresa).aggregate(
            total=Sum('monto')
        )
        total_ingresos = self._num(ingresos_totales['total'])

        # Top servicios (por nombre de producto/descripción)
        top_servicios = list(
            Venta.objects.filter(
                empresa=empresa
            ).values('producto__nombre')
            .annotate(
                total_ventas=Sum('cantidad'),
                ingresos=Sum('monto')
            )
            .order_by('-ingresos')[:5]
        )

        # Servicio promedio por cliente (ingresos / clientes)
        total_clientes = Cliente.objects.filter(empresa=empresa).count()
        valor_promedio_servicio = (total_ingresos / total_clientes) if total_clientes > 0 else 0
        valor_promedio_servicio = round(valor_promedio_servicio, 2)

        # Satisfacción/Calidad (placeholder para futuro)
        calidad_promedio = 0.0

        return {
            'ordenes_totales': ordenes_totales,
            'ordenes_pendientes': ordenes_pendientes,
            'ordenes_completadas': ordenes_completadas,
            'clientes_activos': clientes_activos,
            'total_clientes': total_clientes,
            'total_ingresos': total_ingresos,
            'top_servicios': top_servicios,
            'valor_promedio_servicio': valor_promedio_servicio,
            'calidad_promedio': calidad_promedio,
        }
