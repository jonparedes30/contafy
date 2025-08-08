from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages
from empresa.models import SolicitudAyuda
from empresa.services.notificaciones_service import NotificacionesService

def responder_solicitud_web(request, solicitud_id):
    """Vista web para responder solicitudes directamente"""
    solicitud = get_object_or_404(SolicitudAyuda, id=solicitud_id)
    
    if request.method == 'POST':
        respuesta = request.POST.get('respuesta', '').strip()
        
        if respuesta:
            # Actualizar solicitud
            solicitud.estado = 'resuelto'
            solicitud.respuesta = respuesta
            solicitud.save()
            
            # Enviar email al usuario
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
            
            return HttpResponse(f"""
            <html>
            <head><title>Respuesta Enviada</title></head>
            <body style="font-family: Arial; padding: 20px;">
                <h2>✅ Respuesta Enviada</h2>
                <p>Tu respuesta ha sido enviada correctamente a <strong>{solicitud.usuario.username}</strong>.</p>
                <p>El usuario recibirá un email y verá la respuesta en su bandeja de entrada.</p>
                <hr>
                <p><strong>Solicitud:</strong> {solicitud.asunto}</p>
                <p><strong>Tu respuesta:</strong></p>
                <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
                    {respuesta.replace(chr(10), '<br>')}
                </div>
            </body>
            </html>
            """)
    
    return render(request, 'empresa/responder_solicitud_web.html', {
        'solicitud': solicitud
    })