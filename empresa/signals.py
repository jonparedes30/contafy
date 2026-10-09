from decimal import Decimal

import threading

from django.core.exceptions import ObjectDoesNotExist

from django.db.models.signals import post_save, post_delete, pre_delete
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


# ════════════════════════════════════════════════════════════════════
# AUDITORÍA AUTOMÁTICA — Centro de Empresa
# ════════════════════════════════════════════════════════════════════

def _get_usuario(instance):
    """Usuario de auditoría: modificado_por > creado_por > None."""
    return (
        getattr(instance, 'modificado_por', None)
        or getattr(instance, 'creado_por', None)
    )


def _get_empresa(instance):
    """Empresa de auditoría (para el modelo Empresa: la empresa ES el instance)."""
    if instance.__class__.__name__ == 'Empresa':
        return instance
    try:
        return getattr(instance, 'empresa', None) or None
    except ObjectDoesNotExist:
        # La empresa ya fue borrada (último paso de una cascada): no hay dónde auditar.
        return None


def _get_monto(instance):
    """Extrae monto del instance si lo tiene."""
    monto = getattr(instance, 'monto', None) or getattr(instance, 'monto_pagado', None)
    if monto is None:
        return None
    if isinstance(monto, Decimal):
        return monto
    try:
        return Decimal(str(monto))
    except Exception:
        return None


# Empresas cuyo borrado está en curso (por hilo). Mientras se borra una empresa, la
# cascada elimina sus ventas, usuarios, etc.; auditar esas eliminaciones crearía filas
# que apuntan a la empresa que desaparece y la base rechazaría todo el borrado.
_borrado_en_curso = threading.local()


def _empresas_borrandose():
    if not hasattr(_borrado_en_curso, 'ids'):
        _borrado_en_curso.ids = set()
    return _borrado_en_curso.ids


def _registrar_evento_auditoria(sender, instance, tipo):
    """Lógica común para registrar un evento de auditoría."""
    try:
        from empresa.services.auditoria_service import AuditoriaService
        empresa_id = getattr(instance, 'empresa_id', None) or (instance.pk if sender.__name__ == 'Empresa' else None)
        if tipo == 'eliminar' and empresa_id in _empresas_borrandose():
            return
        empresa = _get_empresa(instance)
        if not empresa:
            return

        descripcion = f"{tipo.capitalize()} de {sender.__name__} #{instance.pk}: {str(instance)[:200]}"
        AuditoriaService.registrar(
            empresa=empresa,
            usuario=_get_usuario(instance),
            tipo=tipo,
            modelo=sender.__name__,
            objeto_id=instance.pk,
            descripcion=descripcion,
            monto=_get_monto(instance),
        )
    except Exception as e:
        # Nunca romper el flujo principal por un fallo de auditoría
        logger.error(f'Error en signal auditoría {sender.__name__}: {e}', exc_info=True)


def conectar_signals_auditoria():
    """
    Conecta signals de auditoría para los modelos auditados.
    Se llama desde EmpresaConfig.ready().
    """
    from empresa.models import (
        Venta, Compra, Gasto, Producto, Capital,
        PagoCuentaPorCobrar, PagoCuentaPorPagar, Empresa,
        Usuario, PoderEmpleado,  # Fix #6: auditar creación/eliminación de empleados y cambios de permisos
    )

    MODELOS_AUDITADOS = [
        Venta, Compra, Gasto, Producto, Capital,
        PagoCuentaPorCobrar, PagoCuentaPorPagar, Empresa,
        Usuario, PoderEmpleado,
    ]

    def _make_save_handler():
        def handler(sender, instance, created, **kwargs):
            tipo = 'crear' if created else 'editar'
            _registrar_evento_auditoria(sender, instance, tipo)
        return handler

    def _make_delete_handler():
        def handler(sender, instance, **kwargs):
            _registrar_evento_auditoria(sender, instance, 'eliminar')
        return handler

    def _empresa_pre_delete(sender, instance, **kwargs):
        _empresas_borrandose().add(instance.pk)

    def _empresa_post_delete(sender, instance, **kwargs):
        _empresas_borrandose().discard(instance.pk)

    # pre_delete de la empresa se emite antes de borrar cualquier objeto de la cascada.
    pre_delete.connect(_empresa_pre_delete, sender=Empresa, weak=False, dispatch_uid='audit_empresa_pre_delete')

    for Modelo in MODELOS_AUDITADOS:
        post_save.connect(
            _make_save_handler(),
            sender=Modelo,
            weak=False,
            dispatch_uid=f'audit_save_{Modelo.__name__}',
        )
        post_delete.connect(
            _make_delete_handler(),
            sender=Modelo,
            weak=False,
            dispatch_uid=f'audit_delete_{Modelo.__name__}',
        )

    # Se conecta después del handler de auditoría para limpiar la marca al final.
    post_delete.connect(_empresa_post_delete, sender=Empresa, weak=False, dispatch_uid='audit_empresa_post_delete')

    logger.info(f'Auditoría conectada para {len(MODELOS_AUDITADOS)} modelos.')