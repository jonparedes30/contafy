from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from empresa.models import SolicitudAyuda
from empresa.services.notificaciones_service import NotificacionesService


@login_required
def responder_solicitud_web(request, solicitud_id):
    """Vista web para responder solicitudes directamente.

    Restringida a staff/superuser (equipo de soporte interno).
    """
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("Solo el equipo de soporte puede responder solicitudes")

    solicitud = get_object_or_404(SolicitudAyuda, id=solicitud_id)

    if request.method == 'POST':
        respuesta = request.POST.get('respuesta', '').strip()

        if respuesta:
            solicitud.estado = 'resuelto'
            solicitud.respuesta = respuesta
            solicitud.save()

            email_contenido = f"""
Hola {solicitud.usuario.get_full_name() or solicitud.usuario.username},

Tienes una respuesta a tu solicitud de ayuda en CONTAFY:

SOLICITUD: {solicitud.asunto}

RESPUESTA:
{respuesta}

Puedes ver esta respuesta en tu panel de CONTAFY > Asistente.

Si necesitas más ayuda, puedes enviar una nueva solicitud.

Saludos,
Equipo CONTAFY
            """.strip()

            if solicitud.usuario.email:
                NotificacionesService.enviar_email(
                    solicitud.usuario.email,
                    f'[CONTAFY] Respuesta a tu solicitud: {solicitud.asunto}',
                    email_contenido,
                    solicitud.empresa
                )

            return render(request, 'empresa/responder_solicitud_web.html', {
                'solicitud': solicitud,
                'enviado': True,
                'respuesta_enviada': respuesta,
            })

    return render(request, 'empresa/responder_solicitud_web.html', {
        'solicitud': solicitud
    })