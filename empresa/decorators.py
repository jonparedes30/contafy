from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from empresa.models import PoderEmpleado

def require_power(power_name):
    """
    Decorador para verificar que el usuario tenga un poder específico
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Si es el dueño, permitir todo
            if hasattr(request.user, 'empresa') and request.user.empresa:
                dueño = request.user.empresa.usuarios.first()
                if request.user.id == dueño.id:
                    return view_func(request, *args, **kwargs)
            
            # Verificar si el usuario tiene el poder requerido
            try:
                poderes = PoderEmpleado.objects.get(empleado=request.user, empresa=request.user.empresa)
                if getattr(poderes, power_name, False):
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, f'No tienes permisos para acceder a esta función.')
                    return redirect('empresa:resumen_financiero')
            except PoderEmpleado.DoesNotExist:
                messages.error(request, 'No tienes permisos configurados.')
                return redirect('empresa:resumen_financiero')
        return _wrapped_view
    return decorator

def require_owner(view_func):
    """
    Decorador para verificar que el usuario sea el dueño de la empresa
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'empresa') and request.user.empresa:
            dueño = request.user.empresa.usuarios.first()
            if request.user.id == dueño.id:
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