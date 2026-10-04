from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from empresa.models import PoderEmpleado


def _obtener_propietario(empresa):
    """
    Devuelve el usuario propietario de la empresa.

    Fix #5: usa el campo explícito `empresa.propietario` en lugar de
    `empresa.usuarios.first()` (que es frágil — dependía del orden de IDs).

    Fallback: si `propietario` es None (datos legacy), auto-cura asignándolo
    al usuario con menor ID y guardándolo en la BD.
    """
    if empresa.propietario_id:
        return empresa.propietario

    # Auto-curar datos legacy
    legacy_owner = empresa.usuarios.order_by('id').first()
    if legacy_owner:
        empresa.propietario = legacy_owner
        empresa.save(update_fields=['propietario'])
    return legacy_owner


def require_power(power_name):
    """
    Decorador para verificar que el usuario tenga un poder específico.
    El dueño siempre tiene acceso a todo.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Validar que tenga empresa asociada
            if not hasattr(request.user, 'empresa') or not request.user.empresa:
                messages.error(request, 'No tienes una empresa asociada.')
                return redirect('empresa:home')

            # Si es el dueño, permitir todo
            propietario = _obtener_propietario(request.user.empresa)
            if propietario and request.user.id == propietario.id:
                return view_func(request, *args, **kwargs)

            # Verificar si el usuario tiene el poder requerido
            try:
                poderes = PoderEmpleado.objects.get(
                    empleado=request.user, empresa=request.user.empresa
                )
                if getattr(poderes, power_name, False):
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'No tienes permisos para acceder a esta función.')
                    return redirect('empresa:resumen_financiero')
            except PoderEmpleado.DoesNotExist:
                messages.error(request, 'No tienes permisos configurados.')
                return redirect('empresa:resumen_financiero')
        return _wrapped_view
    return decorator


def require_owner(view_func):
    """
    Decorador para verificar que el usuario sea el dueño de la empresa.
    Fix #5: usa `empresa.propietario` en lugar de `usuarios.first()`.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'empresa') and request.user.empresa:
            propietario = _obtener_propietario(request.user.empresa)
            if propietario and request.user.id == propietario.id:
                return view_func(request, *args, **kwargs)

        messages.error(request, 'Solo el dueño de la empresa puede acceder a esta función.')
        return redirect('empresa:resumen_financiero')
    return _wrapped_view

def empresa_required(view_func):
    """
    Decorador para verificar que el usuario tenga una empresa asignada
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'empresa') or not request.user.empresa:
            messages.error(request, 'Debes tener una empresa asignada para acceder a esta función.')
            return redirect('empresa:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view