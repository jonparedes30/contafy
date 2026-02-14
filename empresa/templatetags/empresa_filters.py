from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplica dos valores"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='mul')
def mul(value, arg):
    """Alias de multiply para compatibilidad con templates"""
    return multiply(value, arg)

@register.filter
def div(value, arg):
    """Divide value entre arg, devuelve 0 si arg es 0 o inválido"""
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (ValueError, TypeError):
        return 0

@register.filter
def abs(value):
    """Valor absoluto"""
    try:
        return float(value).__abs__()
    except (ValueError, TypeError):
        return 0

@register.filter
def eq(value, arg):
    """Retorna True si value es igual a arg"""
    return str(value) == str(arg) 