from django.db.models.signals import post_save
from django.dispatch import receiver
from empresa.models import CuentaContable
from empresa.services.accounting_setup import ensure_contrapartidas_for_account
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=CuentaContable)
def crear_contrapartidas_al_crear_cuenta(sender, instance, created, **kwargs):
    """
    DESACTIVADO TEMPORALMENTE: Causa recursión infinita.
    Cuando el usuario crea una cuenta nueva, generamos contrapartidas recomendadas.
    """
    # DESACTIVADO - causa recursión infinita
    return
    
    if not created:
        return
    try:
        created_accounts = ensure_contrapartidas_for_account(instance)
        if created_accounts:
            logger.info("Se crearon %s contrapartidas para cuenta %s", len(created_accounts), instance.id)
    except Exception as e:
        logger.exception("Error al crear contrapartidas para cuenta %s: %s", instance.id, e)