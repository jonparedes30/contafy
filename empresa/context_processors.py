from empresa.models import PoderEmpleado

def breadcrumbs(request):
    """Context processor para breadcrumbs"""
    return {}

def user_permissions(request):
    """Context processor para agregar permisos del usuario a todos los templates"""
    context = {
        'is_owner': False,
        'user_powers': None
    }
    
    # Verificar que el usuario tenga empresa (superusuario no tiene)
    if not (request.user.is_authenticated and hasattr(request.user, 'empresa') and request.user.empresa):
        return context
    
    try:
        # Verificar si es propietario
        from empresa.decorators import _obtener_propietario
        propietario = _obtener_propietario(request.user.empresa)
        context['is_owner'] = request.user.id == propietario.id if propietario else False
        
        # Obtener poderes del empleado
        if not context['is_owner']:
            try:
                context['user_powers'] = PoderEmpleado.objects.get(
                    empleado=request.user, 
                    empresa=request.user.empresa
                )
            except PoderEmpleado.DoesNotExist:
                # Crear poderes por defecto si no existen
                context['user_powers'] = PoderEmpleado.objects.create(
                    empleado=request.user,
                    empresa=request.user.empresa,
                    puede_ver_reportes=False,
                    puede_registrar_ventas=False,
                    puede_editar_productos=False,
                    puede_gestionar_cuentas=False,
                    puede_registrar_gastos=False,
                    puede_gestionar_inventario=False,
                    puede_gestionar_metas=False,
                )
        else:
            # Para propietarios, crear un objeto mock con todos los permisos
            class MockPowers:
                puede_ver_reportes = True
                puede_registrar_ventas = True
                puede_editar_productos = True
                puede_gestionar_cuentas = True
                puede_registrar_gastos = True
                puede_gestionar_inventario = True
                puede_gestionar_metas = True
            
            context['user_powers'] = MockPowers()
    except Exception as e:
        # Si falla, retornar contexto vacío sin crashear
        pass
    
    return context

def alertas_navbar(request):
    """Alertas reales para la campana: stock bajo y cuentas por cobrar vencidas."""
    empresa = getattr(request.user, 'empresa', None) if request.user.is_authenticated else None
    if not empresa:
        return {}
    from django.db.models import F
    from django.utils import timezone
    from empresa.models import CuentaPorCobrar, Producto

    try:
        stock_bajo = Producto.objects.filter(
            empresa=empresa, es_servicio=False, stock__lte=F('stock_minimo')
        ).count()
        cxc_vencidas = CuentaPorCobrar.objects.filter(
            empresa=empresa, monto_pendiente__gt=0, fecha_vencimiento__lt=timezone.localdate()
        ).count()
    except Exception:
        return {}
    return {'alertas_navbar': {'stock_bajo': stock_bajo, 'cxc_vencidas': cxc_vencidas,
                               'total': stock_bajo + cxc_vencidas}}


def escaner(request):
    """Opciones del escáner que dependen de la configuración del servidor."""
    from django.conf import settings
    return {'escaner_foto_activa': bool(getattr(settings, 'GOOGLE_VISION_API_KEY', ''))}
