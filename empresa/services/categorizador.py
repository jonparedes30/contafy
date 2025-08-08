"""
Servicio de categorización de gastos.

Para añadir nuevas palabras clave:
- Edita las listas GASTOS_FIJOS_KEYWORDS y GASTOS_VARIABLES_KEYWORDS.
- O bien, pásalas como argumento a las funciones categorizar_gasto o categorizar_gastos_queryset.
- O bien, agrégalas vía el modelo CategoriaGastoKeyword en el admin.

# FUTURO: Panel de configuración de palabras clave por empresa.
"""
from django.db import transaction
import logging
from empresa.models import CategoriaGastoKeyword
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

# Palabras clave parametrizables
gastos_fijos_keywords = [
    _('renta'), _('alquiler'), _('servicios'), _('luz'), _('agua'), _('internet'),
    _('telefono'), _('seguro'), _('licencia'), _('software'), _('mantenimiento'),
    _('limpieza'), _('seguridad'), _('contador'), _('abogado')
]
gastos_variables_keywords = [
    _('material'), _('insumo'), _('papel'), _('tinta'), _('combustible'),
    _('transporte'), _('comida'), _('café'), _('marketing'), _('publicidad'),
    _('comision'), _('bonificacion'), _('premio'), _('regalo')
]

def get_keywords_from_db():
    fijos = list(CategoriaGastoKeyword.objects.filter(categoria='Fijo', activo=True).values_list('palabra', flat=True))
    variables = list(CategoriaGastoKeyword.objects.filter(categoria='Variable', activo=True).values_list('palabra', flat=True))
    return fijos, variables

def categorizar_gasto(gasto, fijos_keywords=None, variables_keywords=None):
    """
    Asigna la categoría a un gasto según su descripción.
    Args:
        gasto (Gasto): instancia de Gasto.
        fijos_keywords (list): lista de palabras clave para fijos.
        variables_keywords (list): lista de palabras clave para variables.
    Returns:
        str: Categoría asignada ('Fijo' o 'Variable').
    """
    if not getattr(gasto, 'descripcion', None):
        logger.warning(f'Gasto sin descripción: id={getattr(gasto, "id", None)}')
        return gasto.categoria  # No cambia

    descripcion_lower = gasto.descripcion.lower()
    # Si no se pasan listas, intenta obtenerlas de la BD
    if fijos_keywords is None or variables_keywords is None:
        fijos, variables = get_keywords_from_db()
        if not fijos or not variables:
            fijos = gastos_fijos_keywords
            variables = gastos_variables_keywords
    else:
        fijos = fijos_keywords
        variables = variables_keywords

    if any(keyword in descripcion_lower for keyword in variables):
        return 'Variable'
    if any(keyword in descripcion_lower for keyword in fijos):
        return 'Fijo'
    return gasto.categoria  # Mantiene la actual si no hay match

@transaction.atomic
def categorizar_gastos_queryset(queryset, fijos_keywords=None, variables_keywords=None):
    """
    Categorización masiva de gastos con atomicidad y logging.
    Args:
        queryset: QuerySet de Gasto.
        fijos_keywords (list): lista de palabras clave para fijos.
        variables_keywords (list): lista de palabras clave para variables.
    Returns:
        dict: resumen de la operación.
    """
    total = queryset.count()
    fijos = 0
    variables = 0
    sin_cambio = 0

    for gasto in queryset:
        categoria_original = gasto.categoria
        nueva_categoria = categorizar_gasto(gasto, fijos_keywords, variables_keywords)
        if nueva_categoria != categoria_original:
            gasto.categoria = nueva_categoria
            gasto.save()
            logger.info(f'Gasto "{gasto.descripcion}" categorizado como {nueva_categoria}')
            if nueva_categoria == 'Fijo':
                fijos += 1
            elif nueva_categoria == 'Variable':
                variables += 1
        else:
            sin_cambio += 1

    return {
        'total': total,
        'fijos': fijos,
        'variables': variables,
        'sin_cambio': sin_cambio,
    } 