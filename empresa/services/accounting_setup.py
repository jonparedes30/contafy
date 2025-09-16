from django.db import transaction
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)

# Lista de contrapartidas por defecto
DEFAULT_CONTRAPARTIDAS = [
    {"codigo_suffix": "CJA", "nombre_tpl": "Caja - {base_nombre}", "tipo": "activo"},
    {"codigo_suffix": "BNK", "nombre_tpl": "Bancos - {base_nombre}", "tipo": "activo"},
    {"codigo_suffix": "VTA", "nombre_tpl": "Ventas - {base_nombre}", "tipo": "ingreso"},
    {"codigo_suffix": "IVA", "nombre_tpl": "IVA repercutido - {base_nombre}", "tipo": "pasivo"},
]

def ensure_contrapartidas_for_account(cuenta):
    """
    Asegura que existan contrapartidas recomendadas para la cuenta dada.
    - Crea las cuentas si no existen (idempotente).
    - Si la clase CuentaContable tiene un campo M2M 'contrapartidas' las vincula.
    - Devuelve la lista de cuentas creadas/aseguradas.
    """
    CuentaContable = cuenta.__class__

    created = []
    with transaction.atomic():
        for conf in DEFAULT_CONTRAPARTIDAS:
            # generar nombre sugerido basado en la cuenta original
            base_nombre = getattr(cuenta, "nombre", "Cuenta")
            proposed_nombre = conf["nombre_tpl"].format(base_nombre=base_nombre)
            
            # Truncar si excede 100 caracteres
            if len(proposed_nombre) > 100:
                proposed_nombre = proposed_nombre[:97] + '...'
            
            # normalizar para evitar duplicados en distinta compañía
            obj, is_created = CuentaContable.objects.get_or_create(
                empresa=cuenta.empresa,
                nombre=proposed_nombre,
                defaults={
                    "tipo": conf.get("tipo", "activo"),
                },
            )
            if is_created:
                created.append(obj)
            
            # Vincular si existe campo contrapartidas en el modelo
            try:
                if hasattr(cuenta, "contrapartidas"):
                    cuenta.contrapartidas.add(obj)
                elif hasattr(cuenta, "add_contrapartida"):
                    cuenta.add_contrapartida(obj)
            except Exception as e:
                logger.debug("No se pudo vincular contrapartida automáticamente: %s", e)
    
    return created