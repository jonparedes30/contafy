from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from empresa.models import Venta, Compra, Gasto, Producto, MovimientoContable, Capital, Usuario, PagoCuentaPorCobrar, PagoCuentaPorPagar
from empresa.decorators import require_power


@login_required
@require_power('puede_ver_reportes')
def asignar_usuarios_auditoria(request):
    """
    Vista temporal para asignar usuarios a registros existentes que tienen creado_por como None.
    Solo accesible para usuarios con permisos de ver reportes.
    """
    if request.method == 'POST':
        empresa = request.user.empresa
        usuario_asignar = request.user  # Usar el usuario actual
        
        # Contar registros sin usuario
        modelos = [
            (Venta, 'Ventas'),
            (Compra, 'Compras'),
            (Gasto, 'Gastos'),
            (Producto, 'Productos'),
            (MovimientoContable, 'Movimientos Contables'),
            (Capital, 'Capital')
        ]
        
        total_actualizados = 0
        detalles = []
        
        for modelo, nombre in modelos:
            registros_sin_usuario = modelo.objects.filter(
                empresa=empresa,
                creado_por__isnull=True
            )
            
            if registros_sin_usuario.exists():
                count = registros_sin_usuario.count()
                registros_sin_usuario.update(creado_por=usuario_asignar)
                total_actualizados += count
                detalles.append(f"{nombre}: {count} registros")
        
        if total_actualizados > 0:
            return render(request, 'empresa/asignacion_completada.html', {
                'total_actualizados': total_actualizados,
                'detalles': detalles,
                'usuario_asignado': usuario_asignar.username
            })
        else:
            return render(request, 'empresa/asignacion_completada.html', {
                'total_actualizados': 0,
                'mensaje': 'No hay registros que necesiten asignación de usuario.'
            })
    
    # GET request - mostrar información
    empresa = request.user.empresa
    
    # Contar registros sin usuario
    modelos = [
        (Venta, 'Ventas'),
        (Compra, 'Compras'),
        (Gasto, 'Gastos'),
        (Producto, 'Productos'),
        (MovimientoContable, 'Movimientos Contables'),
        (Capital, 'Capital')
    ]
    
    resumen = []
    total_sin_usuario = 0
    
    for modelo, nombre in modelos:
        count = modelo.objects.filter(
            empresa=empresa,
            creado_por__isnull=True
        ).count()
        
        if count > 0:
            resumen.append({
                'modelo': nombre,
                'cantidad': count
            })
            total_sin_usuario += count
    
    return render(request, 'empresa/asignar_usuarios_auditoria.html', {
        'resumen': resumen,
        'total_sin_usuario': total_sin_usuario,
        'empresa': empresa
    })


@login_required
@require_power('puede_ver_reportes')
def actividad_reciente(request):
    """
    Vista para mostrar el historial de actividades recientes.
    Solo accesible para usuarios con permisos de ver reportes.
    """
    empresa = request.user.empresa
    
    # Obtener parámetros de filtro
    dias = request.GET.get('dias', '7')  # Por defecto 7 días
    tipo = request.GET.get('tipo', '')   # Filtro por tipo
    usuario = request.GET.get('usuario', '')  # Filtro por usuario
    
    try:
        dias = int(dias)
    except ValueError:
        dias = 7
    
    # Calcular fecha límite
    fecha_limite = timezone.now() - timedelta(days=dias)
    
    # Construir consultas base con distinct para evitar duplicados
    ventas = Venta.objects.filter(
        empresa=empresa,
        creado_en__gte=fecha_limite
    ).select_related('creado_por', 'producto').distinct()
    
    compras = Compra.objects.filter(
        empresa=empresa,
        creado_en__gte=fecha_limite
    ).select_related('creado_por', 'producto').distinct()
    
    gastos = Gasto.objects.filter(
        empresa=empresa,
        creado_en__gte=fecha_limite
    ).select_related('creado_por').distinct()
    
    productos = Producto.objects.filter(
        empresa=empresa,
        creado_en__gte=fecha_limite
    ).select_related('creado_por').distinct()
    
    capitales = Capital.objects.filter(
        empresa=empresa,
        creado_en__gte=fecha_limite
    ).select_related('creado_por').distinct()
    
    pagos_cobrar = PagoCuentaPorCobrar.objects.filter(
        empresa=empresa,
        creado_en__gte=fecha_limite
    ).select_related('creado_por', 'cuenta_por_cobrar__cliente').distinct()
    
    pagos_pagar = PagoCuentaPorPagar.objects.filter(
        empresa=empresa,
        creado_en__gte=fecha_limite
    ).select_related('creado_por', 'cuenta_por_pagar__proveedor').distinct()
    
    # Aplicar filtros adicionales
    if tipo:
        if tipo == 'ventas':
            compras = gastos = productos = capitales = pagos_cobrar = pagos_pagar = []
        elif tipo == 'compras':
            ventas = gastos = productos = capitales = pagos_cobrar = pagos_pagar = []
        elif tipo == 'gastos':
            ventas = compras = productos = capitales = pagos_cobrar = pagos_pagar = []
        elif tipo == 'productos':
            ventas = compras = gastos = capitales = pagos_cobrar = pagos_pagar = []
        elif tipo == 'capital':
            ventas = compras = gastos = productos = pagos_cobrar = pagos_pagar = []
        elif tipo == 'cobros':
            ventas = compras = gastos = productos = capitales = pagos_pagar = []
        elif tipo == 'pagos':
            ventas = compras = gastos = productos = capitales = pagos_cobrar = []
    
    if usuario:
        ventas = ventas.filter(creado_por__username__icontains=usuario)
        compras = compras.filter(creado_por__username__icontains=usuario)
        gastos = gastos.filter(creado_por__username__icontains=usuario)
        productos = productos.filter(creado_por__username__icontains=usuario)
        capitales = capitales.filter(creado_por__username__icontains=usuario)
        pagos_cobrar = pagos_cobrar.filter(creado_por__username__icontains=usuario)
        pagos_pagar = pagos_pagar.filter(creado_por__username__icontains=usuario)
    
    # Combinar todas las actividades y ordenar por fecha
    actividades = []
    ids_procesados = set()  # Para evitar duplicados
    
    for venta in ventas:
        # Solo incluir si tiene fecha de creación y no está duplicado
        venta_id = f"venta_{venta.id}"
        if venta.creado_en and venta_id not in ids_procesados:
            ids_procesados.add(venta_id)
            actividades.append({
                'fecha': venta.creado_en,
                'tipo': 'Venta',
                'descripcion': f"Venta de {venta.producto.nombre} - ${venta.monto}",
                'usuario': venta.creado_por or None,
                'usuario_nombre': venta.creado_por.username if venta.creado_por else 'Sistema',
                'objeto': venta,
                'cliente': venta.cliente_display
            })
    
    for compra in compras:
        # Solo incluir si tiene fecha de creación y no está duplicado
        compra_id = f"compra_{compra.id}"
        if compra.creado_en and compra_id not in ids_procesados:
            ids_procesados.add(compra_id)
            actividades.append({
                'fecha': compra.creado_en,
                'tipo': 'Compra',
                'descripcion': f"Compra de {compra.producto.nombre} - ${compra.monto}",
                'usuario': compra.creado_por or None,
                'usuario_nombre': compra.creado_por.username if compra.creado_por else 'Sistema',
                'objeto': compra,
                'proveedor': compra.proveedor_display
            })
    
    for gasto in gastos:
        # Solo incluir si tiene fecha de creación y no está duplicado
        gasto_id = f"gasto_{gasto.id}"
        if gasto.creado_en and gasto_id not in ids_procesados:
            ids_procesados.add(gasto_id)
            actividades.append({
                'fecha': gasto.creado_en,
                'tipo': 'Gasto',
                'descripcion': f"{gasto.descripcion} - ${gasto.monto}",
                'usuario': gasto.creado_por or None,
                'usuario_nombre': gasto.creado_por.username if gasto.creado_por else 'Sistema',
                'objeto': gasto,
                'categoria': gasto.categoria
            })
    
    for producto in productos:
        # Solo incluir si tiene fecha de creación y no está duplicado
        producto_id = f"producto_{producto.id}"
        if producto.creado_en and producto_id not in ids_procesados:
            ids_procesados.add(producto_id)
            actividades.append({
                'fecha': producto.creado_en,
                'tipo': 'Producto',
                'descripcion': f"Producto creado: {producto.nombre}",
                'usuario': producto.creado_por or None,
                'usuario_nombre': producto.creado_por.username if producto.creado_por else 'Sistema',
                'objeto': producto
            })
    

    for capital in capitales:
        # Solo incluir si tiene fecha de creación y no está duplicado
        capital_id = f"capital_{capital.id}"
        if capital.creado_en and capital_id not in ids_procesados:
            ids_procesados.add(capital_id)
            actividades.append({
                'fecha': capital.creado_en,
                'tipo': 'Capital',
                'descripcion': f"Inversión de capital - ${capital.monto}",
                'usuario': capital.creado_por or None,
                'usuario_nombre': capital.creado_por.username if capital.creado_por else 'Sistema',
                'objeto': capital
            })
    
    for pago in pagos_cobrar:
        pago_id = f"pago_cobrar_{pago.id}"
        if pago.creado_en and pago_id not in ids_procesados:
            ids_procesados.add(pago_id)
            actividades.append({
                'fecha': pago.creado_en,
                'tipo': 'Cobro de Crédito',
                'descripcion': f"Cobro de ${pago.monto_pagado} de {pago.cuenta_por_cobrar.cliente.nombre} por {pago.get_metodo_pago_display()}",
                'usuario': pago.creado_por or None,
                'usuario_nombre': pago.creado_por.username if pago.creado_por else 'Sistema',
                'objeto': pago,
                'cliente': pago.cuenta_por_cobrar.cliente.nombre
            })
    
    for pago in pagos_pagar:
        pago_id = f"pago_pagar_{pago.id}"
        if pago.creado_en and pago_id not in ids_procesados:
            ids_procesados.add(pago_id)
            actividades.append({
                'fecha': pago.creado_en,
                'tipo': 'Pago de Crédito',
                'descripcion': f"Pago de ${pago.monto_pagado} a {pago.cuenta_por_pagar.proveedor.nombre} por {pago.get_metodo_pago_display()}",
                'usuario': pago.creado_por or None,
                'usuario_nombre': pago.creado_por.username if pago.creado_por else 'Sistema',
                'objeto': pago,
                'proveedor': pago.cuenta_por_pagar.proveedor.nombre
            })
    
    # Eliminar duplicados finales basándose en contenido único
    actividades_unicas = []
    contenidos_vistos = set()
    
    for actividad in actividades:
        # Crear clave única basada en tipo, fecha, descripción y usuario
        clave_unica = f"{actividad['tipo']}_{actividad['fecha'].isoformat()}_{actividad['descripcion']}_{actividad['usuario_nombre']}"
        
        if clave_unica not in contenidos_vistos:
            contenidos_vistos.add(clave_unica)
            actividades_unicas.append(actividad)
    
    # Usar la lista limpia
    actividades = actividades_unicas
    
    # Ordenar por fecha (más reciente primero)
    actividades.sort(key=lambda x: x['fecha'], reverse=True)
    
    # Estadísticas
    total_actividades = len(actividades)
    usuarios_activos = set()
    for actividad in actividades:
        if actividad['usuario_nombre'] and actividad['usuario_nombre'] != 'Sistema':
            usuarios_activos.add(actividad['usuario_nombre'])
    
    context = {
        'actividades': actividades,
        'total_actividades': total_actividades,
        'usuarios_activos': len(usuarios_activos),
        'dias_filtro': dias,
        'tipo_filtro': tipo,
        'usuario_filtro': usuario,
        'empresa': empresa
    }
    
    return render(request, 'empresa/actividad_reciente.html', context) 