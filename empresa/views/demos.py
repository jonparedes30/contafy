from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from empresa.models import (
    Usuario, Venta, Producto, OrdenProduccion
)

DEMO_USERNAMES = ['demo_comercio', 'demo_manufactura', 'demo_servicios']


def acceso_rapido_demo(request, username):
    """Loguea automáticamente con la cuenta demo indicada y redirige al home."""
    if username not in DEMO_USERNAMES:
        messages.error(request, 'Demo no encontrada.')
        return redirect('empresa:landing')

    # Si ya hay sesión activa con esta misma cuenta demo, ir directo
    if request.user.is_authenticated and request.user.username == username:
        return redirect('empresa:home')

    try:
        usuario = Usuario.objects.get(username=username)
    except Usuario.DoesNotExist:
        messages.warning(request, 'La cuenta demo no está disponible. Contáctanos.')
        return redirect('empresa:landing')

    # Autenticar sin contraseña (confiamos en que son cuentas demo controladas)
    usuario.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, usuario)
    return redirect('empresa:home')


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
