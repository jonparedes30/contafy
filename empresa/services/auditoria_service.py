"""
AuditoriaService — Servicio centralizado para auditoría y estadísticas del Centro de Empresa.

Funciones principales:
- registrar(): crea un RegistroAuditoria (usado por signals automáticos)
- obtener_actividades(): pagina y filtra el timeline de actividades
- obtener_estadisticas_empresa(): KPIs NIIF correctos (ventas netas, costo de ventas, utilidad real)
- obtener_resumen_equipo(): empleados con su última actividad y métricas del mes

Ver docs y plan de Centro de Empresa.
"""
import logging
from datetime import timedelta
from decimal import Decimal

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max, Count, Q, Sum, OuterRef, Subquery
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuditoriaService:

    @staticmethod
    def registrar(empresa, usuario, tipo, modelo, objeto_id, descripcion,
                  monto=None, metadatos=None):
        """
        Crea un RegistroAuditoria. Idempotente — si falla, NO rompe el flujo
        del caller. Diseñado para llamarse desde signals.

        Args:
            empresa: instancia de Empresa (obligatorio)
            usuario: instancia de Usuario o None (Sistema)
            tipo: 'crear' | 'editar' | 'eliminar'
            modelo: nombre del modelo (str)
            objeto_id: PK del objeto (puede ser None si ya se eliminó)
            descripcion: texto descriptivo
            monto: opcional, monto monetario asociado
            metadatos: dict opcional con cambios antes/después
        """
        from empresa.models import RegistroAuditoria

        if not empresa:
            return None

        try:
            return RegistroAuditoria.objects.create(
                empresa=empresa,
                usuario=usuario,
                tipo_operacion=tipo,
                modelo=modelo,
                objeto_id=objeto_id,
                descripcion=descripcion[:1000],  # cap
                monto=monto,
                metadatos=metadatos or {},
            )
        except Exception as e:
            logger.error(f'Error registrando auditoría: {e}', exc_info=True)
            return None

    @staticmethod
    def obtener_actividades(empresa, dias=7, tipo=None, usuario_filtro=None,
                            page=1, per_page=50):
        """
        Paginador de actividades con filtros aplicados.

        Args:
            empresa: instancia de Empresa
            dias: ventana de tiempo (default 7)
            tipo: filtro por modelo (None, 'Venta', 'Compra', 'Gasto', ...)
            usuario_filtro: busca en username, first_name, last_name (icontains)
            page, per_page: paginación

        Returns:
            dict con 'page_obj' (Paginator.page), 'total', 'usuarios_activos',
            'dias', 'tipo', 'usuario_filtro' (echo de filtros)
        """
        from empresa.models import RegistroAuditoria

        fecha_limite = timezone.now() - timedelta(days=int(dias))

        qs = (
            RegistroAuditoria.objects
            .filter(empresa=empresa, fecha__gte=fecha_limite)
            .select_related('usuario')
            .order_by('-fecha')
        )

        if tipo:
            qs = qs.filter(modelo__iexact=tipo)

        if usuario_filtro:
            qs = qs.filter(
                Q(usuario__username__icontains=usuario_filtro) |
                Q(usuario__first_name__icontains=usuario_filtro) |
                Q(usuario__last_name__icontains=usuario_filtro)
            )

        # Estadísticas previas a paginar
        total = qs.count()
        usuarios_activos = (
            qs.values('usuario').exclude(usuario__isnull=True).distinct().count()
        )

        # Paginación
        paginator = Paginator(qs, per_page)
        try:
            page_obj = paginator.page(page)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.page(1)

        return {
            'page_obj': page_obj,
            'total': total,
            'usuarios_activos': usuarios_activos,
            'dias': dias,
            'tipo': tipo or '',
            'usuario_filtro': usuario_filtro or '',
        }

    @staticmethod
    def obtener_estadisticas_empresa(empresa, mes=None, anio=None):
        """
        KPIs financieros con cálculo NIIF correcto:
        - ventas_netas: Sum('monto_neto') sobre Venta
        - costo_ventas: Sum('monto_neto') sobre Compra
        - gastos_operativos: Sum('monto') sobre Gasto
        - utilidad_operativa: ventas_netas - costo_ventas - gastos_operativos

        Usa timezone-aware datetime para evitar desfases.
        """
        from empresa.models import Venta, Compra, Gasto, Producto

        ahora = timezone.localtime(timezone.now())
        mes = mes or ahora.month
        anio = anio or ahora.year

        rango = {
            'fecha__year': anio,
            'fecha__month': mes,
        }

        ventas_qs = Venta.objects.filter(empresa=empresa, **rango)
        ventas_netas = (
            ventas_qs.aggregate(t=Sum('monto_neto'))['t']
            or ventas_qs.aggregate(t=Sum('monto'))['t']
            or Decimal('0')
        )

        compras_qs = Compra.objects.filter(empresa=empresa, **rango)
        costo_ventas = (
            compras_qs.aggregate(t=Sum('monto_neto'))['t']
            or compras_qs.aggregate(t=Sum('monto'))['t']
            or Decimal('0')
        )

        gastos_operativos = (
            Gasto.objects.filter(empresa=empresa, **rango)
            .aggregate(t=Sum('monto'))['t']
            or Decimal('0')
        )

        utilidad_operativa = (
            float(ventas_netas) - float(costo_ventas) - float(gastos_operativos)
        )

        return {
            'mes': mes,
            'anio': anio,
            'ventas_netas': float(ventas_netas),
            'costo_ventas': float(costo_ventas),
            'gastos_operativos': float(gastos_operativos),
            'utilidad_operativa': utilidad_operativa,
            'margen_operativo': (
                (utilidad_operativa / float(ventas_netas) * 100)
                if float(ventas_netas) > 0 else 0
            ),
            'total_empleados': empresa.usuarios.count(),
            'total_productos': Producto.objects.filter(empresa=empresa).count(),
            'ventas_count': ventas_qs.count(),
            'compras_count': compras_qs.count(),
        }

    @staticmethod
    def obtener_resumen_equipo(empresa):
        """
        Lista de empleados con su última actividad registrada y conteo
        de actividades en el mes actual.

        Returns: lista de Usuario con campos anotados: `ultima_actividad`
        y `actividades_mes`. Ordenado por actividad reciente primero.
        """
        from empresa.models import RegistroAuditoria

        ahora = timezone.localtime(timezone.now())
        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        empleados_qs = (
            empresa.usuarios
            .annotate(
                ultima_actividad=Subquery(
                    RegistroAuditoria.objects
                    .filter(empresa=empresa, usuario=OuterRef('pk'))
                    .order_by('-fecha').values('fecha')[:1]
                ),
                actividades_mes=Count(
                    'auditorias_realizadas',
                    filter=Q(
                        auditorias_realizadas__empresa=empresa,
                        auditorias_realizadas__fecha__gte=inicio_mes,
                    ),
                ),
            )
            .order_by('-actividades_mes', '-ultima_actividad')
        )

        return list(empleados_qs)
