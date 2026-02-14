from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from empresa.models import (
    Usuario, Venta, Producto, OrdenProduccion
)

def demos_disponibles(request):
    """Muestra las demos disponibles y permite acceso rápido"""
    
    demos = [
        {
            'tipo': 'Comercio',
            'nombre': 'Minimarket Don Pepe',
            'descripcion': 'Tienda de abarrotes con inventario, ventas y control de stock',
            'ubicacion': 'Quito, Pichincha',
            'username': 'demo_comercio',
            'password': 'demo123',
            'icon': 'bi-shop',
            'color': 'primary',
            'caracteristicas': [
                '6 productos en inventario',
                '50+ ventas registradas',
                'Control de proveedores',
                'Gestión de clientes',
                'Reportes financieros'
            ]
        },
        {
            'tipo': 'Manufactura',
            'nombre': 'Panadería El Buen Pan',
            'descripcion': 'Panadería artesanal con producción y ventas',
            'ubicacion': 'Cuenca, Azuay',
            'username': 'demo_manufactura',
            'password': 'demo123',
            'icon': 'bi-basket',
            'color': 'warning',
            'caracteristicas': [
                '6 productos manufacturados',
                '60+ ventas realizadas',
                'Control de materias primas',
                'Costos de producción',
                'Órdenes de producción'
            ]
        },
        {
            'tipo': 'Servicios',
            'nombre': 'Peluquería Estilo & Belleza',
            'descripcion': 'Salón de belleza con servicios y productos',
            'ubicacion': 'Guayaquil, Guayas',
            'username': 'demo_servicios',
            'password': 'demo123',
            'icon': 'bi-scissors',
            'color': 'success',
            'caracteristicas': [
                '7 servicios disponibles',
                '80+ servicios prestados',
                'Venta de productos',
                'Clientes frecuentes',
                'Agenda de citas'
            ]
        }
    ]
    
    context = {
        'demos': demos
    }
    
    return render(request, 'empresa/demos_disponibles.html', context)

def acceso_rapido_demo(request, username):
    """Acceso rápido a una cuenta demo"""
    try:
        usuario = Usuario.objects.get(username=username)
        
        # Autenticar automáticamente
        usuario.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, usuario)
        
        messages.success(request, f'¡Bienvenido a la demo de {usuario.empresa.nombre}! Explora todas las funcionalidades.')
        return redirect('empresa:home')
        
    except Usuario.DoesNotExist:
        messages.error(request, 'Demo no encontrada. Por favor, ejecuta el comando crear_demos primero.')
        return redirect('empresa:entrada_beta')


def selector_demo(request):
    """Página con selector único para elegir una demo y entrar automáticamente"""
    demos = [
        {
            'tipo': 'Comercio',
            'nombre': 'Minimarket Don Pepe',
            'descripcion': 'Tienda de abarrotes con inventario, ventas y control de stock',
            'ubicacion': 'Quito, Pichincha',
            'username': 'demo_comercio',
            'password': 'demo1234',
            'icon': 'bi-shop',
            'color': 'primary',
        },
        {
            'tipo': 'Manufactura',
            'nombre': 'Panadería El Buen Pan',
            'descripcion': 'Panadería artesanal con producción y ventas',
            'ubicacion': 'Cuenca, Azuay',
            'username': 'demo_manufactura',
            'password': 'demo1234',
            'icon': 'bi-basket',
            'color': 'warning',
        },
        {
            'tipo': 'Servicios',
            'nombre': 'Consultora Demo Ltda.',
            'descripcion': 'Consultoría y servicios profesionales',
            'ubicacion': 'Guayaquil, Guayas',
            'username': 'demo_servicios',
            'password': 'demo1234',
            'icon': 'bi-briefcase',
            'color': 'success',
        }
    ]

    # Añadir métricas de últimos 3 meses para cada demo
    three_months_ago = timezone.now() - timedelta(days=90)
    enhanced = []
    for d in demos:
        stats = {'ventas_3m': 0, 'productos': 0, 'ordenes': 0}
        try:
            usuario = Usuario.objects.filter(username=d['username']).first()
            if usuario and usuario.empresa:
                empresa = usuario.empresa
                stats['ventas_3m'] = Venta.objects.filter(empresa=empresa, fecha__gte=three_months_ago).count()
                stats['productos'] = Producto.objects.filter(empresa=empresa).count()
                stats['ordenes'] = OrdenProduccion.objects.filter(empresa=empresa).count()
        except Exception:
            pass
        d.update(stats)
        enhanced.append(d)

    context = {'demos': enhanced}
    return render(request, 'empresa/demos_selector.html', context)
