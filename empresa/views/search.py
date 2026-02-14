
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse

# Mapas de navegación definidos globalmente para reutilización
NAV_MAP = {
    'ventas': 'empresa:listar_ventas',
    'venta': 'empresa:listar_ventas',
    'facturas': 'empresa:listar_ventas',
    'compras': 'empresa:listar_compras',
    'compra': 'empresa:listar_compras',
    'gastos': 'empresa:listar_gastos',
    'gasto': 'empresa:listar_gastos',
    'productos': 'empresa:listar_productos',
    'producto': 'empresa:listar_productos',
    'inventario': 'empresa:inventario',
    'stock': 'empresa:inventario',
    'balance': 'empresa:balance_general',
    'estado': 'empresa:estado_resultados',
    'resultados': 'empresa:estado_resultados',
    'pnl': 'empresa:estado_resultados',
    'flujo': 'empresa:flujo_caja',
    'caja': 'empresa:flujo_caja',
    'metas': 'empresa:gestionar_metas',
    'objetivos': 'empresa:gestionar_metas',
    'dashboard': 'empresa:dashboard',
    'inicio': 'empresa:dashboard',
    'home': 'empresa:dashboard',
    'configuracion': 'empresa:editar_empresa',
    'empresa': 'empresa:editar_empresa',
    'perfil': 'empresa:editar_usuario',
    'usuario': 'empresa:editar_usuario',
    'ayuda': 'empresa:asistente_ayuda',
    'asistente': 'empresa:asistente_ayuda',
    'ia': 'empresa:agente_ia',
    'bot': 'empresa:agente_ia',
    'agente': 'empresa:agente_ia',
}

CREATE_MAP = {
    'nueva venta': 'empresa:crear_venta',
    'crear venta': 'empresa:crear_venta',
    'nueva factura': 'empresa:crear_venta',
    'crear factura': 'empresa:crear_venta',
    'nuevo producto': 'empresa:crear_producto',
    'crear producto': 'empresa:crear_producto',
    'nuevo gasto': 'empresa:crear_gasto',
    'crear gasto': 'empresa:crear_gasto',
    'nueva compra': 'empresa:crear_compra',
    'crear compra': 'empresa:crear_compra',
}

@login_required
def global_search(request):
    query = request.GET.get('q', '').strip().lower()
    
    # 3. Verificar coincidencias exactas o parciales para redirección directa
    if query:
        # Primero verificar acciones de creación específicas
        for key, url_name in CREATE_MAP.items():
            if key in query:
                return redirect(url_name)
        
        # Luego verificar navegación general
        for key, url_name in NAV_MAP.items():
            if key in query: # "balance general" matches "balance"
                return redirect(url_name)

    context = {
        'query': query,
    }
    return render(request, 'empresa/search_results.html', context)

@login_required
def search_suggestions_api(request):
    """
    API para devolver sugerencias de búsqueda en tiempo real (JSON).
    """
    query = request.GET.get('q', '').strip().lower()
    results = []

    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    # Buscar en acciones de creación
    for key, url_name in CREATE_MAP.items():
        if query in key:
            results.append({
                'title': key.title(),
                'url': reverse(url_name),
                'type': 'Acción',
                'icon': 'bi-plus-circle'
            })

    # Buscar en navegación
    for key, url_name in NAV_MAP.items():
        if query in key:
            results.append({
                'title': key.title(),
                'url': reverse(url_name),
                'type': 'Ir a',
                'icon': 'bi-arrow-right-short'
            })
            
    # Limitar resultados para no saturar
    return JsonResponse({'results': results[:8]})
