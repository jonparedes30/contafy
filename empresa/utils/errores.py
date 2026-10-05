"""Mensajes de error seguros para mostrar al usuario."""
import logging

from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger('empresa.errores')

MENSAJE_GENERICO = 'No se pudo completar la operación. Inténtalo de nuevo; si persiste, contacta a soporte.'


def mensaje_error(exc, publico=MENSAJE_GENERICO):
    """Registra la excepción y devuelve un texto apto para el usuario.

    Llamar dentro del bloque `except` (para que el log incluya el traceback).
    - ValidationError: sus mensajes ya están escritos para el usuario.
    - Cualquier otra: mensaje genérico. `str(exc)` puede contener SQL, rutas o
      claves de API, así que solo se agrega en modo DEBUG.
    """
    if isinstance(exc, ValidationError):
        return ' '.join(exc.messages)
    logger.exception('Error no controlado: %s', exc)
    if getattr(settings, 'DEBUG', False):
        return f'{publico} [DEBUG: {type(exc).__name__}: {exc}]'
    return publico
