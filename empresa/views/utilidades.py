from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def validar_ruc(ruc):
    """Valida un RUC ecuatoriano simple (solo longitud y tipo numérico)"""
    if not ruc.isdigit() or len(ruc) != 13:
        raise ValidationError(_('El RUC debe contener 13 dígitos numéricos.'))

def redondear_decimal(valor, decimales=2):
    """Redondea valores numéricos a N decimales"""
    try:
        return round(float(valor), decimales)
    except (TypeError, ValueError):
        return 0.00

def formato_moneda(valor):
    """Devuelve un valor con formato monetario"""
    return "${:,.2f}".format(valor)

def requiere_empresa(view_func):
    """
    Decorador que verifica que el usuario tenga una empresa asociada.
    Si no la tiene, redirige a crear empresa.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.empresa:
            messages.warning(request, 'Necesitas tener una empresa asociada para acceder a esta función.')
            return redirect('crear_empresa')
        return view_func(request, *args, **kwargs)
    return wrapper
