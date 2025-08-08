from django import template
from django.conf import settings

register = template.Library()

@register.filter
def currency(value):
    """Formatea un valor como moneda en dólares"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.simple_tag
def currency_symbol():
    """Retorna el símbolo de moneda configurado"""
    return getattr(settings, 'CURRENCY_SYMBOL', '$')

@register.simple_tag
def currency_code():
    """Retorna el código de moneda configurado"""
    return getattr(settings, 'CURRENCY_CODE', 'USD')