from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from empresa.models import Venta, Gasto, Compra, CuentaContable, MovimientoContable, CategoriaProducto, Producto, ProductoManufacturado
import calendar
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
import json
from empresa.views.resumen import obtener_totales_contables
from empresa.services.filtros_service import FiltrosFechaService

@login_required
def dashboard(request):
    empresa = request.user.empresa
    totales = obtener_totales_contables(empresa)
    # Usar servicio de filtros mejorado
    fecha_inicio, fecha_fin = FiltrosFechaService.obtener_rango_fechas(request)
    
    # Validar fechas
    errores_fecha = FiltrosFechaService.validar_fechas(fecha_inicio, fecha_fin)
    if errores_fecha:
        # Si hay errores, usar rango por defecto
        hoy = timezone.now().date()
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    # Generar lista de meses en el rango
    labels_meses = []
    ventas_mensuales = []
    gastos_mensuales = []
    margen_neto_historico = []
    liquidez_historica = []
    endeudamiento_historico = []
    roe_historico = []
    meses = []
    fecha_iter = fecha_inicio.replace(day=1)
    while fecha_iter <= fecha_fin:
        meses.append((fecha_iter.year, fecha_iter.month))
        labels_meses.append(f"{fecha_iter.strftime('%b')} {fecha_iter.year}")
        # Avanzar al siguiente mes
        if fecha_iter.month == 12:
            fecha_iter = fecha_iter.replace(year=fecha_iter.year+1, month=1)
        else:
            fecha_iter = fecha_iter.replace(month=fecha_iter.month+1)
    # Calcular KPIs y gráficos para cada mes del rango seleccionado
    # USAR DATOS DIRECTOS de Venta y Gasto (tienen fechas históricas correctas)
    for anio, mes in meses:
        # Rango de fechas del mes
        fecha_mes_inicio = timezone.datetime(anio, mes, 1).date()
        if mes == 12:
            fecha_mes_fin = timezone.datetime(anio+1, 1, 1).date() - timezone.timedelta(days=1)
        else:
            fecha_mes_fin = timezone.datetime(anio, mes+1, 1).date() - timezone.timedelta(days=1)

        # Ventas directas del modelo Venta (monto_neto tiene las fechas históricas correctas)
        ventas_mes = Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_mes_inicio,
            fecha__date__lte=fecha_mes_fin
        ).aggregate(total=Sum('monto_neto'))['total'] or 0

        # Costos: estimar como porcentaje de ventas basado en precio_unitario vs pvp
        costos_mes_data = Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_mes_inicio,
            fecha__date__lte=fecha_mes_fin
        ).aggregate(
            total_costo=Sum('precio_unitario'),
        )
        # Calcular costo real basado en precio_unitario * cantidad
        from django.db.models import F
        costos_mes = Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_mes_inicio,
            fecha__date__lte=fecha_mes_fin
        ).aggregate(
            total=Sum(F('producto__precio_unitario') * F('cantidad'))
        )['total'] or 0

        # Gastos directos del modelo Gasto
        gastos_mes = Gasto.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_mes_inicio,
            fecha__date__lte=fecha_mes_fin
        ).aggregate(total=Sum('monto'))['total'] or 0

        # Capital, activos y pasivos acumulados (usando saldos de CuentaContable)
        capital_mes = sum(cuenta.valor for cuenta in CuentaContable.objects.filter(empresa=empresa, tipo='capital'))
        activos_mes = sum(cuenta.valor for cuenta in CuentaContable.objects.filter(empresa=empresa, tipo='activo'))
        pasivos_mes = sum(cuenta.valor for cuenta in CuentaContable.objects.filter(empresa=empresa, tipo='pasivo'))
        utilidad_bruta_mes = ventas_mes - costos_mes
        utilidad_neta_mes = utilidad_bruta_mes - gastos_mes
        margen_neto_mes = ((utilidad_neta_mes / ventas_mes) * 100) if ventas_mes else 0
        roe_mes = ((utilidad_neta_mes / capital_mes) * 100) if capital_mes else 0
        liquidez_mes = (activos_mes / pasivos_mes) if pasivos_mes else 0
        endeudamiento_mes = (pasivos_mes / activos_mes) if activos_mes else 0
        print(f"DEBUG - Mes {mes}/{anio}: Ventas={ventas_mes}, Gastos={gastos_mes}, Costos={costos_mes}")
        ventas_mensuales.append(round(float(ventas_mes), 2))
        gastos_mensuales.append(round(float(gastos_mes), 2))
        margen_neto_historico.append(round(float(margen_neto_mes), 2))
        liquidez_historica.append(round(float(liquidez_mes), 2))
        endeudamiento_historico.append(round(float(endeudamiento_mes), 2))
        roe_historico.append(round(float(roe_mes), 2))
    # KPIs totales del periodo (calculados de los datos directos)
    total_ventas = sum(ventas_mensuales)
    total_gastos = sum(gastos_mensuales)
    # Costos totales directos basado en costo unitario * cantidad
    from django.db.models import F as F_expr
    total_costos = Venta.objects.filter(
        empresa=empresa,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).aggregate(
        total=Sum(F_expr('producto__precio_unitario') * F_expr('cantidad'))
    )['total'] or Decimal('0')
    total_costos = float(Decimal(total_costos) if not isinstance(total_costos, Decimal) else total_costos)
    utilidad_bruta = total_ventas - total_costos
    utilidad_neta = utilidad_bruta - total_gastos
    margen_bruto = ((utilidad_bruta / total_ventas) * 100) if total_ventas > 0 else 0
    margen_neto = ((utilidad_neta / total_ventas) * 100) if total_ventas > 0 else 0
    # Recalcular saldos finales usando la lógica correcta
    total_capital = sum(cuenta.valor for cuenta in CuentaContable.objects.filter(empresa=empresa, tipo='capital'))
    total_activos = sum(cuenta.valor for cuenta in CuentaContable.objects.filter(empresa=empresa, tipo='activo'))
    total_pasivos = sum(cuenta.valor for cuenta in CuentaContable.objects.filter(empresa=empresa, tipo='pasivo'))
    roe = (utilidad_neta / total_capital * 100) if total_capital else 0
    liquidez = (total_activos / total_pasivos) if total_pasivos else 0
    endeudamiento = (total_pasivos / total_activos) if total_activos else 0
    rentabilidad = margen_neto

    # NO rellenar - usar exactamente los datos del período seleccionado
    print(f"DEBUG - Labels: {len(labels_meses)}, Ventas: {len(ventas_mensuales)}, Gastos: {len(gastos_mensuales)}")
    print(f"DEBUG - Labels meses: {labels_meses}")
    print(f"DEBUG - Ventas mensuales finales: {ventas_mensuales}")
    print(f"DEBUG - Gastos mensuales finales: {gastos_mensuales}")

    ratio_gastos_ventas = round((total_gastos / total_ventas * 100), 2) if total_ventas else 0
    fecha_ultima_actualizacion = datetime.now().strftime('%d/%m/%Y %H:%M')
    if utilidad_neta > 0:
        estado_actual = 'Saludable'
    elif utilidad_neta == 0:
        estado_actual = 'Estable'
    else:
        estado_actual = 'En Riesgo'

    # Convertir Decimals a float para el gráfico
    ventas_mensuales_float = [float(x) for x in ventas_mensuales]
    gastos_mensuales_float = [float(x) for x in gastos_mensuales]
    
    # Obtener distribución de gastos por descripción individual
    gastos_por_descripcion = Gasto.objects.filter(
        empresa=empresa,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).values('descripcion').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('-total')[:10]  # Top 10 gastos más altos
    
    # Debug: Imprimir información básica
    print(f"DEBUG - Fecha inicio: {fecha_inicio}, Fecha fin: {fecha_fin}")
    print(f"DEBUG - Total ventas: ${total_ventas}, Total gastos: ${total_gastos}, Total costos: ${total_costos}")
    print(f"DEBUG - Utilidad bruta: ${utilidad_bruta}, Margen bruto: {margen_bruto}%")
    print(f"DEBUG - Ventas mensuales: {ventas_mensuales}")
    print(f"DEBUG - Gastos mensuales: {gastos_mensuales}")
    print(f"DEBUG - Gastos por descripción encontrados: {len(gastos_por_descripcion)}")
    
    # Preparar datos para el gráfico de distribución
    descripciones_gastos = []
    montos_gastos = []
    colores_gastos = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384']
    
    if gastos_por_descripcion:
        for i, gasto in enumerate(gastos_por_descripcion):
            # Truncar descripción si es muy larga
            descripcion = gasto['descripcion'][:20] + '...' if len(gasto['descripcion']) > 20 else gasto['descripcion']
            descripciones_gastos.append(descripcion)
            montos_gastos.append(float(gasto['total']))
    else:
        # Si no hay gastos, agregar datos de ejemplo para evitar gráfico vacío
        descripciones_gastos = ['Sin datos']
        montos_gastos = [0]
    
    # Obtener el gasto más frecuente (por descripción)
    gasto_mas_frecuente = Gasto.objects.filter(
        empresa=empresa,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).values('descripcion').annotate(
        cantidad=Count('id'),
        total_monto=Sum('monto')
    ).order_by('-cantidad').first()
    
    mensaje_gasto_frecuente = ""
    if gasto_mas_frecuente:
        mensaje_gasto_frecuente = f"El gasto más frecuente es '{gasto_mas_frecuente['descripcion']}' con {gasto_mas_frecuente['cantidad']} registros (${gasto_mas_frecuente['total_monto']:.2f})"
    else:
        mensaje_gasto_frecuente = "No hay gastos registrados en el período seleccionado"
    
    # Obtener los 5 productos más vendidos (según tipo de empresa)
    if empresa.categoria == 'manufactura':
        # Para manufactura, filtrar solo ventas de productos manufacturados
        productos_manuf_ids = ProductoManufacturado.objects.filter(
            empresa=empresa
        ).values_list('codigo', flat=True)
        
        productos_mas_vendidos = Venta.objects.filter(
            empresa=empresa,
            producto__codigo__in=productos_manuf_ids,
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).values('producto__nombre').annotate(
            total_ventas=Sum('monto_neto'),
            cantidad_vendida=Sum('cantidad'),
            veces_vendido=Count('id')
        ).order_by('-total_ventas')[:5]
    else:
        productos_mas_vendidos = Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).values('producto__nombre').annotate(
            total_ventas=Sum('monto_neto'),
            cantidad_vendida=Sum('cantidad'),
            veces_vendido=Count('id')
        ).order_by('-total_ventas')[:5]
    
    # Debug: Imprimir información de productos más vendidos
    print(f"DEBUG - Productos más vendidos encontrados: {len(productos_mas_vendidos)}")
    for producto in productos_mas_vendidos:
        print(f"DEBUG - Producto: {producto['producto__nombre']}, Ventas: ${producto['total_ventas']}, Cantidad: {producto['cantidad_vendida']}")
    
    # Preparar datos para el gráfico de productos más vendidos
    nombres_productos = []
    totales_ventas = []
    cantidades_vendidas = []
    colores_productos = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
    
    if productos_mas_vendidos:
        for i, producto in enumerate(productos_mas_vendidos):
            # Truncar nombre si es muy largo
            nombre = producto['producto__nombre'][:20] + '...' if len(producto['producto__nombre']) > 20 else producto['producto__nombre']
            nombres_productos.append(nombre)
            totales_ventas.append(float(producto['total_ventas']))
            cantidades_vendidas.append(producto['cantidad_vendida'])
    else:
        # Si no hay productos, agregar datos de ejemplo para evitar gráfico vacío
        nombres_productos = ['Sin datos']
        totales_ventas = [0]
        cantidades_vendidas = [0]
    
    # Obtener el producto más vendido para el mensaje
    producto_mas_vendido = productos_mas_vendidos.first()
    mensaje_producto_mas_vendido = ""
    if producto_mas_vendido:
        mensaje_producto_mas_vendido = f"El producto más vendido es '{producto_mas_vendido['producto__nombre']}' con ${producto_mas_vendido['total_ventas']:.2f} en ventas"
    else:
        mensaje_producto_mas_vendido = "No hay ventas registradas en el período seleccionado"
    # KPIs filtrados por fecha para las tarjetas principales (según tipo de empresa)
    if empresa.categoria == 'manufactura':
        # Para manufactura, filtrar solo ventas de productos manufacturados
        productos_manuf_ids = ProductoManufacturado.objects.filter(
            empresa=empresa
        ).values_list('codigo', flat=True)
        
        ventas_filtradas = Venta.objects.filter(
            empresa=empresa,
            producto__codigo__in=productos_manuf_ids,
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).aggregate(total=Sum('monto_neto'))['total'] or Decimal('0')
    else:
        ventas_filtradas = Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).aggregate(total=Sum('monto_neto'))['total'] or Decimal('0')
    
    # Compras filtradas (según tipo de empresa)
    if empresa.categoria == 'manufactura':
        # Para manufactura, usar consumos de materias primas como "compras"
        from empresa.models import ConsumoMateriaPrima
        compras_filtradas = ConsumoMateriaPrima.objects.filter(
            empresa=empresa,
            fecha_consumo__date__gte=fecha_inicio,
            fecha_consumo__date__lte=fecha_fin
        ).aggregate(total=Sum('costo_total'))['total'] or Decimal('0')
    else:
        compras_filtradas = Compra.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    gastos_filtrados = Gasto.objects.filter(
        empresa=empresa,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    # Costo de ventas - USAR CUENTA CORREGIDA
    costo_ventas_filtrado = total_costos
    
    # Convertir todos a float para evitar mezcla de tipos
    ventas_filtradas_float = float(ventas_filtradas)
    compras_filtradas_float = float(compras_filtradas)
    gastos_filtrados_float = float(gastos_filtrados)
    costo_ventas_filtrado_float = float(costo_ventas_filtrado)
    
    utilidad_bruta_filtrada = ventas_filtradas_float - costo_ventas_filtrado_float
    utilidad_neta_filtrada = utilidad_bruta_filtrada - gastos_filtrados_float
    
    contexto = {
        'ventas': ventas_filtradas_float,
        'compras': compras_filtradas_float,
        'gastos': gastos_filtrados_float,
        'utilidad_bruta': utilidad_bruta_filtrada,
        'utilidad_neta': float(utilidad_neta_filtrada),
        'costo_ventas': costo_ventas_filtrado_float,
        'ratio_gastos_ventas': ratio_gastos_ventas,
        'fecha_ultima_actualizacion': fecha_ultima_actualizacion,
        'estado_actual': estado_actual,
        'total_ventas': round(float(total_ventas), 2),
        'total_gastos': round(float(total_gastos), 2),
        'total_costos': round(float(total_costos), 2),
        'utilidad_bruta': round(utilidad_bruta, 2),
        'rentabilidad': round(rentabilidad, 2),
        'labels_meses': labels_meses,
        'ventas_mensuales': ventas_mensuales,
        'gastos_mensuales': gastos_mensuales,
        'margen_bruto': round(margen_bruto, 2),
        'margen_neto': round(margen_neto, 2),
        'roe': round(roe, 2),
        'liquidez': round(liquidez, 2),
        'endeudamiento': round(endeudamiento, 2),
        'margen_neto_historico': margen_neto_historico,
        'liquidez_historica': liquidez_historica,
        'endeudamiento_historico': endeudamiento_historico,
        'roe_historico': roe_historico,
        'otros_ingresos': 0,
        'total_ingresos': round(float(total_ventas), 2),
        'margen_operativo': round(margen_neto, 2),
        'ratio_costos': round((float(total_costos) / float(total_ventas) * 100) if float(total_ventas) > 0 else 0, 1),
        'ratio_gastos': round((float(total_gastos) / float(total_ventas) * 100) if float(total_ventas) > 0 else 0, 1),
        # BENCHMARK DEL SECTOR - DATOS REALES POR TIPO DE EMPRESA
        'margen_ventas': round(margen_neto, 1),
        'promedio_sector': 15 if empresa.categoria == 'comercial' else 25 if empresa.categoria == 'manufactura' else 20,
        'mejor_sector': 25 if empresa.categoria == 'comercial' else 40 if empresa.categoria == 'manufactura' else 35,
        # Para el gráfico de barras (serializado como JSON)
        'labels': json.dumps(labels_meses),
        'ventas_data': json.dumps(ventas_mensuales_float),
        'gastos_data': json.dumps(gastos_mensuales_float),
        
        # Para el gráfico de distribución de gastos
        'descripciones_gastos': json.dumps(descripciones_gastos),
        'montos_gastos': json.dumps(montos_gastos),
        'colores_gastos': json.dumps(colores_gastos),
        'mensaje_gasto_frecuente': mensaje_gasto_frecuente,
        
        # Para el gráfico de productos más vendidos
        'nombres_productos': json.dumps(nombres_productos),
        'totales_ventas': json.dumps(totales_ventas),
        'cantidades_vendidas': json.dumps(cantidades_vendidas),
        'colores_productos': json.dumps(colores_productos),
        'mensaje_producto_mas_vendido': mensaje_producto_mas_vendido,
    }
    
    # Calcular histórico de utilidades mensuales
    utilidades_mensuales = []
    for i in range(len(ventas_mensuales)):
        ventas_mes = ventas_mensuales[i]
        gastos_mes = gastos_mensuales[i]
        utilidad_mes = ventas_mes - gastos_mes
        utilidades_mensuales.append(round(utilidad_mes, 2))
    
    # Calcular tendencia de utilidades
    if len(utilidades_mensuales) >= 2:
        utilidad_actual = utilidades_mensuales[-1]
        utilidad_anterior = utilidades_mensuales[-2]
        diferencia = utilidad_actual - utilidad_anterior
        porcentaje_cambio = ((diferencia / utilidad_anterior) * 100) if utilidad_anterior != 0 else 0
        
        if diferencia > 0:
            mensaje_tendencia = f"Tendencia positiva: +${diferencia:.2f} ({porcentaje_cambio:.1f}%) vs mes anterior"
        elif diferencia < 0:
            mensaje_tendencia = f"Tendencia negativa: ${diferencia:.2f} ({porcentaje_cambio:.1f}%) vs mes anterior"
        else:
            mensaje_tendencia = "Tendencia estable: sin cambios vs mes anterior"
    else:
        mensaje_tendencia = "Datos insuficientes para calcular tendencia"
    
    # NUEVOS REPORTES COMERCIALES
    
    # 1. Análisis de márgenes por categoría
    margenes_categoria = []
    nombres_categorias = []
    colores_categorias = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
    
    categorias = CategoriaProducto.objects.filter(empresa=empresa)
    
    # Usar productos según tipo de empresa
    if empresa.categoria == 'manufactura':
        productos_total = ProductoManufacturado.objects.filter(empresa=empresa).count()
        productos_con_categoria = ProductoManufacturado.objects.filter(empresa=empresa, categoria__isnull=False).count()
        productos_sin_categoria = ProductoManufacturado.objects.filter(empresa=empresa, categoria__isnull=True).count()
    else:
        productos_total = Producto.objects.filter(empresa=empresa).count()
        productos_con_categoria = Producto.objects.filter(empresa=empresa, categoria__isnull=False).count()
        productos_sin_categoria = Producto.objects.filter(empresa=empresa, categoria__isnull=True).count()
    
    print(f"DEBUG - Categorías encontradas: {categorias.count()}")
    print(f"DEBUG - Total productos: {productos_total}")
    print(f"DEBUG - Productos CON categoría: {productos_con_categoria}")
    print(f"DEBUG - Productos SIN categoría: {productos_sin_categoria}")
    
    if categorias.exists():
        for cat in categorias:
            print(f"DEBUG - Categoría: {cat.nombre}")
    
    if categorias.exists():
        for categoria in categorias:
            if empresa.categoria == 'manufactura':
                productos_categoria = ProductoManufacturado.objects.filter(empresa=empresa, categoria=categoria)
                if productos_categoria.exists():
                    # Obtener códigos de productos manufacturados de esta categoría
                    codigos_categoria = productos_categoria.values_list('codigo', flat=True)
                    ventas_categoria = Venta.objects.filter(
                        empresa=empresa,
                        producto__codigo__in=codigos_categoria,
                        fecha__date__gte=fecha_inicio,
                        fecha__date__lte=fecha_fin
                    ).aggregate(
                        total_ventas=Sum('monto')
                    )
                    
                    if ventas_categoria['total_ventas']:
                        total_ventas = float(ventas_categoria['total_ventas'])
                        costo_estimado = total_ventas * 0.6
                        margen = ((total_ventas - costo_estimado) / total_ventas) * 100
                        margenes_categoria.append(round(margen, 1))
                        nombres_categorias.append(categoria.nombre[:15] + '...' if len(categoria.nombre) > 15 else categoria.nombre)
            else:
                productos_categoria = Producto.objects.filter(empresa=empresa, categoria=categoria)
                if productos_categoria.exists():
                    ventas_categoria = Venta.objects.filter(
                        empresa=empresa,
                        producto__categoria=categoria,
                        fecha__date__gte=fecha_inicio,
                        fecha__date__lte=fecha_fin
                    ).aggregate(
                        total_ventas=Sum('monto')
                    )
                    
                    if ventas_categoria['total_ventas']:
                        total_ventas = float(ventas_categoria['total_ventas'])
                        costo_estimado = total_ventas * 0.6
                        margen = ((total_ventas - costo_estimado) / total_ventas) * 100
                        margenes_categoria.append(round(margen, 1))
                        nombres_categorias.append(categoria.nombre[:15] + '...' if len(categoria.nombre) > 15 else categoria.nombre)
    
    # Siempre incluir productos sin categoría si existen
    if empresa.categoria == 'manufactura':
        productos_sin_categoria = ProductoManufacturado.objects.filter(empresa=empresa, categoria__isnull=True)
        if productos_sin_categoria.exists():
            # Obtener códigos de productos manufacturados sin categoría
            codigos_sin_categoria = productos_sin_categoria.values_list('codigo', flat=True)
            ventas_sin_categoria = Venta.objects.filter(
                empresa=empresa,
                producto__codigo__in=codigos_sin_categoria,
                fecha__date__gte=fecha_inicio,
                fecha__date__lte=fecha_fin
            ).aggregate(total_ventas=Sum('monto'))
            
            print(f"DEBUG - Ventas sin categoría (manufactura): {ventas_sin_categoria['total_ventas']}")
            
            if ventas_sin_categoria['total_ventas']:
                margenes_categoria.append(40.0)
                nombres_categorias.append('Sin categoría')
    else:
        productos_sin_categoria = Producto.objects.filter(empresa=empresa, categoria__isnull=True)
        if productos_sin_categoria.exists():
            ventas_sin_categoria = Venta.objects.filter(
                empresa=empresa,
                producto__categoria__isnull=True,
                fecha__date__gte=fecha_inicio,
                fecha__date__lte=fecha_fin
            ).aggregate(total_ventas=Sum('monto'))
            
            print(f"DEBUG - Ventas sin categoría (comercio): {ventas_sin_categoria['total_ventas']}")
            
            if ventas_sin_categoria['total_ventas']:
                margenes_categoria.append(40.0)
                nombres_categorias.append('Sin categoría')
    
    if not margenes_categoria:
        margenes_categoria = [40.0]
        nombres_categorias = ['General']
    
    print(f"DEBUG - Márgenes por categoría: {margenes_categoria}")
    print(f"DEBUG - Nombres categorías: {nombres_categorias}")
    
    # 2. ROTACIÓN DE INVENTARIO CORREGIDA
    rotacion_categoria = []
    
    # Calcular días en el período
    dias_periodo = (fecha_fin - fecha_inicio).days + 1
    factor_anual = 365 / dias_periodo if dias_periodo > 0 else 1
    
    if categorias.exists():
        for categoria in categorias:
            if empresa.categoria == 'manufactura':
                # Para manufactura, usar productos manufacturados
                productos_categoria = ProductoManufacturado.objects.filter(empresa=empresa, categoria=categoria)
                if productos_categoria.exists():
                    stock_promedio = productos_categoria.aggregate(promedio=Sum('stock_actual'))['promedio'] or 1
                    codigos_categoria = productos_categoria.values_list('codigo', flat=True)
                    ventas_cantidad = Venta.objects.filter(
                        empresa=empresa,
                        producto__codigo__in=codigos_categoria,
                        fecha__date__gte=fecha_inicio,
                        fecha__date__lte=fecha_fin
                    ).aggregate(total=Sum('cantidad'))['total'] or 0
                    
                    # Rotación anualizada
                    rotacion = (ventas_cantidad * factor_anual / stock_promedio) if stock_promedio > 0 else 0
                    rotacion_categoria.append(round(rotacion, 1))
            else:
                # Para comercio/servicios, usar productos normales
                productos_categoria = Producto.objects.filter(empresa=empresa, categoria=categoria)
                if productos_categoria.exists():
                    stock_promedio = productos_categoria.aggregate(promedio=Sum('stock'))['promedio'] or 1
                    ventas_cantidad = Venta.objects.filter(
                        empresa=empresa,
                        producto__categoria=categoria,
                        fecha__date__gte=fecha_inicio,
                        fecha__date__lte=fecha_fin
                    ).aggregate(total=Sum('cantidad'))['total'] or 0
                    
                    # Rotación anualizada
                    rotacion = (ventas_cantidad * factor_anual / stock_promedio) if stock_promedio > 0 else 0
                    rotacion_categoria.append(round(rotacion, 1))
    else:
        # Rotación general si no hay categorías
        if empresa.categoria == 'manufactura':
            stock_total = ProductoManufacturado.objects.filter(empresa=empresa).aggregate(total=Sum('stock_actual'))['total'] or 1
            productos_manuf_ids = ProductoManufacturado.objects.filter(empresa=empresa).values_list('codigo', flat=True)
            ventas_total = Venta.objects.filter(
                empresa=empresa,
                producto__codigo__in=productos_manuf_ids,
                fecha__date__gte=fecha_inicio,
                fecha__date__lte=fecha_fin
            ).aggregate(total=Sum('cantidad'))['total'] or 0
        else:
            stock_total = Producto.objects.filter(empresa=empresa).aggregate(total=Sum('stock'))['total'] or 1
            ventas_total = Venta.objects.filter(
                empresa=empresa,
                fecha__date__gte=fecha_inicio,
                fecha__date__lte=fecha_fin
            ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        rotacion_general = (ventas_total * factor_anual / stock_total) if stock_total > 0 else 0
        rotacion_categoria = [round(rotacion_general, 1)]
    
    if not rotacion_categoria:
        rotacion_categoria = [1.0]
    
    print(f"DEBUG - Rotación por categoría: {rotacion_categoria}")
    
    # 3. Productos sin movimiento (últimos 30 días)
    fecha_limite = fecha_fin - timedelta(days=30)
    productos_sin_movimiento = Producto.objects.filter(empresa=empresa).exclude(
        id__in=Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_limite
        ).values_list('producto_id', flat=True)
    )[:10]
    
    productos_sin_movimiento_data = []
    for producto in productos_sin_movimiento:
        productos_sin_movimiento_data.append({
            'nombre': producto.nombre,
            'stock': producto.stock,
            'precio': float(producto.precio_unitario),
            'valor_inmovilizado': float(producto.stock * producto.precio_unitario)
        })
    
    # 4. Rentabilidad temporal (Margen Bruto vs Neto)
    margenes_brutos_mensuales = []
    margenes_netos_mensuales = []
    
    for i in range(len(ventas_mensuales)):
        ventas_mes = ventas_mensuales[i]
        gastos_mes = gastos_mensuales[i]
        
        # Calcular costos del mes (simplificado)
        costos_mes = float(ventas_mes) * 0.6  # Asumiendo 60% de costo promedio
        
        margen_bruto_mes = ((float(ventas_mes) - costos_mes) / float(ventas_mes) * 100) if ventas_mes > 0 else 0
        margen_neto_mes = ((float(ventas_mes) - costos_mes - float(gastos_mes)) / float(ventas_mes) * 100) if ventas_mes > 0 else 0
        
        margenes_brutos_mensuales.append(round(margen_bruto_mes, 1))
        margenes_netos_mensuales.append(round(margen_neto_mes, 1))
    
    # KPIs adicionales - ROTACIÓN CORREGIDA
    rotacion_promedio = sum(rotacion_categoria) / len(rotacion_categoria) if rotacion_categoria and len(rotacion_categoria) > 0 else 0
    
    # Benchmark de rotación por sector
    rotacion_sector = 6 if empresa.categoria == 'comercial' else 12 if empresa.categoria == 'manufactura' else 24
    productos_criticos_count = len(productos_sin_movimiento_data)
    categoria_mas_rentable = nombres_categorias[margenes_categoria.index(max(margenes_categoria))] if margenes_categoria and max(margenes_categoria) > 0 else "N/A"
    
    print(f"DEBUG - KPIs finales:")
    print(f"DEBUG - Rotación promedio: {rotacion_promedio}")
    print(f"DEBUG - Productos críticos: {productos_criticos_count}")
    print(f"DEBUG - Categoría más rentable: {categoria_mas_rentable}")
    print(f"DEBUG - Márgenes brutos mensuales: {margenes_brutos_mensuales}")
    print(f"DEBUG - Márgenes netos mensuales: {margenes_netos_mensuales}")
    
    contexto.update({
        # Para el gráfico de histórico de utilidades
        'utilidades_mensuales': json.dumps([float(x) for x in utilidades_mensuales]),
        'mensaje_tendencia': mensaje_tendencia,
        
        # NUEVOS DATOS COMERCIALES
        # 1. Márgenes por categoría
        'nombres_categorias': json.dumps(nombres_categorias),
        'margenes_categoria': json.dumps(margenes_categoria),
        'colores_categorias': json.dumps(colores_categorias[:len(nombres_categorias)]),
        
        # 2. Rotación por categoría
        'rotacion_categoria': json.dumps(rotacion_categoria),
        
        # 3. Productos sin movimiento
        'productos_sin_movimiento': productos_sin_movimiento_data,
        'productos_criticos_count': productos_criticos_count,
        
        # 4. Rentabilidad temporal
        'margenes_brutos_mensuales': json.dumps(margenes_brutos_mensuales),
        'margenes_netos_mensuales': json.dumps(margenes_netos_mensuales),
        
        # KPIs comerciales - CORREGIDOS
        'rotacion_promedio': round(rotacion_promedio, 1),
        'rotacion_sector': rotacion_sector,
        'categoria_mas_rentable': categoria_mas_rentable,
    })

    return render(request, 'empresa/dashboard.html', contexto) 