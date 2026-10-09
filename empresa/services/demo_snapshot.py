"""Foto y restauración de las empresas demo oficiales.

Regla de las demos: lo que hace un visitante no se conserva. Cada 24 h la demo
vuelve exactamente a su estado original, se haya creado, editado o borrado lo
que sea (incluidos trabajadores y la propia empresa).

- guardar_foto(): serializa todo lo que cuelga de la empresa demo (lo mismo que
  borraría empresa.delete()) y lo guarda en DemoSnapshot.
- restaurar(): borra la empresa completa y vuelve a cargar la foto con las
  mismas claves primarias; luego actualiza las fechas para que la actividad sea
  reciente.
- restaurar_si_vencida(): lo anterior solo si pasaron más de 24 h; se llama al
  entrar a una demo, así no depende de un cron.
"""
import logging
from datetime import timedelta

from django.core import serializers
from django.db import DEFAULT_DB_ALIAS, transaction
from django.db.models.deletion import Collector
from django.utils import timezone

logger = logging.getLogger(__name__)

HORAS_ENTRE_RESETS = 24
# La auditoría de la demo empieza vacía en cada restauración.
MODELOS_EXCLUIDOS = {'RegistroAuditoria'}


def _objetos_de_empresa(empresa):
    """Todos los objetos que se borrarían junto con la empresa."""
    collector = Collector(using=DEFAULT_DB_ALIAS)
    collector.collect([empresa])
    objetos = []
    for modelo, instancias in collector.data.items():
        if modelo.__name__ not in MODELOS_EXCLUIDOS:
            objetos.extend(instancias)
    for queryset in collector.fast_deletes:
        if queryset.model.__name__ not in MODELOS_EXCLUIDOS:
            objetos.extend(queryset)
    return objetos


def guardar_foto(username):
    """Guarda (o reemplaza) la foto de la demo de `username`. Devuelve el DemoSnapshot."""
    from empresa.models import DemoSnapshot, Usuario

    usuario = Usuario.objects.select_related('empresa').get(username=username)
    if not usuario.empresa:
        raise ValueError(f'{username} no tiene empresa: no hay nada que fotografiar')
    objetos = _objetos_de_empresa(usuario.empresa)
    foto, _ = DemoSnapshot.objects.update_or_create(
        username=username,
        defaults={
            'datos': serializers.serialize('json', objetos),
            'total_objetos': len(objetos),
            'ultimo_reset': timezone.now(),
        },
    )
    logger.info('Foto de la demo %s guardada (%s objetos)', username, len(objetos))
    return foto


def restaurar(username, solo_si_vencida=False):
    """Devuelve la demo a su foto. Devuelve True si restauró, False si no hacía falta o no hay foto."""
    from empresa.management.commands.reset_demos import rejuvenecer
    from empresa.models import DemoSnapshot, Usuario

    with transaction.atomic():
        # El bloqueo evita que dos visitantes que entran a la vez restauren dos veces.
        foto = DemoSnapshot.objects.select_for_update().filter(username=username).first()
        if not foto:
            return False
        if solo_si_vencida and foto.ultimo_reset and \
                timezone.now() - foto.ultimo_reset < timedelta(hours=HORAS_ENTRE_RESETS):
            return False

        usuario = Usuario.objects.select_related('empresa').filter(username=username).first()
        if usuario and usuario.empresa:
            usuario.empresa.delete()          # cascada: datos, trabajadores y el propio dueño
        elif usuario:
            usuario.delete()

        # Las claves foráneas son diferidas dentro de la transacción: el orden no importa.
        for objeto in serializers.deserialize('json', foto.datos):
            objeto.save()

        empresa = Usuario.objects.get(username=username).empresa
        dias = rejuvenecer(empresa)
        foto.ultimo_reset = timezone.now()
        foto.save(update_fields=['ultimo_reset'])

    logger.info('Demo %s restaurada desde su foto (fechas desplazadas %s días)', username, dias)
    return True


def restaurar_si_vencida(username):
    """Restaura la demo si pasaron más de 24 h desde la última vez. Nunca rompe el acceso."""
    try:
        return restaurar(username, solo_si_vencida=True)
    except Exception:
        logger.exception('No se pudo restaurar la demo %s', username)
        return False
