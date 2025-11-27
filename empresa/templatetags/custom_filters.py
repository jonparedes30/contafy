"""
Filtros personalizados para templates
"""
from django import template

register = template.Library()


@register.filter
def dict_lookup(dict_obj, key):
    """
    Busca un valor en un diccionario o atributo en un objeto.
    Útil para acceder a atributos dinámicos en templates.
    
    Uso: {{ item|dict_lookup:column.key }}
    """
    if isinstance(dict_obj, dict):
        return dict_obj.get(key, '')
    
    # Intentar acceder como atributo de objeto
    try:
        return getattr(dict_obj, key, '')
    except (AttributeError, TypeError):
        return ''


@register.filter
def truncatewords(value, count):
    """
    Trunca texto a N palabras y agrega '...' si es más largo.
    """
    if not value:
        return ''
    
    words = str(value).split()
    if len(words) > count:
        return ' '.join(words[:count]) + '...'
    return value
