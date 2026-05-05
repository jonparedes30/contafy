from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from empresa.models import Venta, Gasto, Producto, Compra, PoderEmpleado
from empresa.decorators import require_power


@login_required
@require_power('puede_registrar_ventas')
def dashboard_ventas(request):
    """
    Dashboard específico para empleados de ventas.
    Muestra ventas del día, ranking personal y botón rápido para registrar ventas.
    """
    empresa = request.user.empresa
    hoy = timezone.now().date()
    
    # Ventas del día
    ventas_hoy = Venta.objects.filter(
        empresa=empresa,
        fecha__date=hoy
    ).aggregate(
        total_ventas=Count('id'),
        monto_total=Sum('total')
    )
    
    # Ventas del mes actual
    mes_actual = hoy.replace(day=1)
    ventas_mes = Venta.objects.filter(
        empresa=empresa,
        fecha__gte=mes_actual
    ).aggregate(
        total_ventas=Count('id'),
        monto_total=Sum('total')
    )
    
    # Últimas ventas
    ultimas_ventas = Venta.objects.filter(
        empresa=empresa
    ).order_by('-fecha')[:5]
    
    context = {
        'ventas_hoy': ventas_hoy,
        'ventas_mes': ventas_mes,
        'ultimas_ventas': ultimas_ventas,
        'hoy': hoy,
    }
    
    return render(request, 'empresa/dashboards/dashboard_ventas.html', context)


@login_required
@require_power('puede_gestionar_inventario')
def dashboard_inventario(request):
    """
    Dashboard específico para responsables de inventario.
    Muestra alertas de stock bajo, últimas entradas/salidas y botón rápido.
    """
    empresa = request.user.empresa
    
    # Productos con stock bajo (menos de 10 unidades)
    productos_stock_bajo = Producto.objects.filter(
        empresa=empresa,
        stock__lt=10
    ).order_by('stock')[:10]
    
    # Últimas compras (entradas)
    ultimas_compras = Compra.objects.filter(
        empresa=empresa
    ).order_by('-fecha')[:5]
    
    # Últimas ventas (salidas)
    ultimas_ventas = Venta.objects.filter(
        empresa=empresa
    ).order_by('-fecha')[:5]
    
    # Resumen de stock
    total_productos = Producto.objects.filter(empresa=empresa).count()
    productos_sin_stock = Producto.objects.filter(empresa=empresa, stock=0).count()
    
    context = {
        'productos_stock_bajo': productos_stock_bajo,
        'ultimas_compras': ultimas_compras,
        'ultimas_ventas': ultimas_ventas,
        'total_productos': total_productos,
        'productos_sin_stock': productos_sin_stock,
    }
    
    return render(request, 'empresa/dashboards/dashboard_inventario.html', context)


@login_required
def dashboard_gastos(request):
    """
    Dashboard específico para asistentes contables.
    Muestra gastos pendientes, conciliaciones y botón rápido para registrar gastos.
    """
    empresa = request.user.empresa
    
    # Verificar permisos
    poderes = PoderEmpleado.objects.get(empleado=request.user, empresa=empresa)
    if not (poderes.puede_registrar_gastos or poderes.puede_gestionar_cuentas):
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('empresa:home')
    
    # Gastos del mes actual
    mes_actual = timezone.now().replace(day=1)
    gastos_mes = Gasto.objects.filter(
        empresa=empresa,
        fecha__gte=mes_actual
    ).aggregate(
        total_gastos=Count('id'),
        monto_total=Sum('monto')
    )
    
    # Últimos gastos
    ultimos_gastos = Gasto.objects.filter(
        empresa=empresa
    ).order_by('-fecha')[:10]
    
    # Gastos por categoría (top 5)
    gastos_por_categoria = Gasto.objects.filter(
        empresa=empresa,
        fecha__gte=mes_actual
    ).values('categoria__nombre').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('-total')[:5]
    
    context = {
        'gastos_mes': gastos_mes,
        'ultimos_gastos': ultimos_gastos,
        'gastos_por_categoria': gastos_por_categoria,
        'puede_registrar_gastos': poderes.puede_registrar_gastos,
        'puede_gestionar_cuentas': poderes.puede_gestionar_cuentas,
    }
    
    return render(request, 'empresa/dashboards/dashboard_gastos.html', context)


@login_required
@require_power('puede_editar_productos')
def dashboard_productos(request):
    """
    Dashboard específico para gestores de productos.
    Muestra estadísticas de productos y botón rápido para crear/editar.
    """
    empresa = request.user.empresa
    
    # Estadísticas de productos
    total_productos = Producto.objects.filter(empresa=empresa).count()
    productos_activos = Producto.objects.filter(empresa=empresa, activo=True).count()
    productos_sin_stock = Producto.objects.filter(empresa=empresa, stock=0).count()
    
    # Productos más vendidos
    productos_mas_vendidos = Producto.objects.filter(
        empresa=empresa,
        venta__isnull=False
    ).annotate(
        total_ventas=Count('venta')
    ).order_by('-total_ventas')[:5]
    
    # Productos recientes
    productos_recientes = Producto.objects.filter(
        empresa=empresa
    ).order_by('-fecha_creacion')[:5]
    
    context = {
        'total_productos': total_productos,
        'productos_activos': productos_activos,
        'productos_sin_stock': productos_sin_stock,
        'productos_mas_vendidos': productos_mas_vendidos,
        'productos_recientes': productos_recientes,
    }
    
    return render(request, 'empresa/dashboards/dashboard_productos.html', context)


@login_required
@require_power('puede_gestionar_metas')
def dashboard_metas(request):
    """
    Dashboard específico para gestores de metas.
    Muestra progreso de metas y alertas.
    """
    empresa = request.user.empresa
    
    # Obtener metas del mes/año actual (las más recientes primero)
    from empresa.models import MetaFinanciera
    from django.utils import timezone as tz
    ahora = tz.now()
    metas_activas = MetaFinanciera.objects.filter(
        empresa=empresa,
        mes=ahora.month,
        anio=ahora.year
    ).order_by('-actualizado_en')[:5]
    
    # Notificaciones no leídas
    from empresa.models import NotificacionMeta
    notificaciones = NotificacionMeta.objects.filter(
        empresa=empresa,
        leida=False
    ).order_by('-fecha_creacion')[:5]
    
    context = {
        'metas_activas': metas_activas,
        'notificaciones': notificaciones,
    }
    
    return render(request, 'empresa/dashboards/dashboard_metas.html', context)


@login_required
def dashboard_basico(request):
    """
    Dashboard básico para usuarios sin permisos específicos.
    Muestra información general sin datos sensibles.
    """
    empresa = request.user.empresa
    
    # Información básica de la empresa
    total_empleados = empresa.usuarios.count()
    
    # Última actividad (sin mostrar datos específicos)
    ultima_venta = Venta.objects.filter(empresa=empresa).order_by('-fecha').first()
    ultima_compra = Compra.objects.filter(empresa=empresa).order_by('-fecha').first()
    ultimo_gasto = Gasto.objects.filter(empresa=empresa).order_by('-fecha').first()
    
    context = {
        'empresa': empresa,
        'total_empleados': total_empleados,
        'ultima_venta': ultima_venta,
        'ultima_compra': ultima_compra,
        'ultimo_gasto': ultimo_gasto,
    }
    
    return render(request, 'empresa/dashboards/dashboard_basico.html', context) 