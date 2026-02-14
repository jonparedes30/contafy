# empresa/sandbox_mode.py
"""Módulo para controlar el modo sandbox del sistema."""

from django.conf import settings

def is_sandbox():
    """
    Determina si el sistema está en modo sandbox.
    En modo sandbox no se envían emails ni notificaciones externas.
    """
    # Por defecto, considerar sandbox si DEBUG está activo
    return getattr(settings, 'DEBUG', True)