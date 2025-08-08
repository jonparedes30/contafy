from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from empresa.models import SolicitudAyuda
from empresa.services.notificaciones_service import NotificacionesService
import json

@login_required
def asistente_ayuda(request):
    """Vista del asistente de ayuda automatizado global para comercio y manufactura"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tipo_ayuda = data.get('tipo')
            asunto = data.get('asunto', 'Solicitud de ayuda')
            mensaje = data.get('mensaje')
            
            # Crear registro en base de datos
            solicitud = SolicitudAyuda.objects.create(
                usuario=request.user,
                empresa=request.user.empresa,
                tipo=tipo_ayuda,
                asunto=asunto,
                mensaje=mensaje
            )
            
            # Por ahora solo crear la solicitud (sin conversación hasta migrar DB)
            
            # Enviar correo personalizado
            email_asunto = f"[CONTAFY] {asunto} - {request.user.empresa.nombre}"
            email_contenido = f"""
🏢 EMPRESA: {request.user.empresa.nombre}
👤 USUARIO: {request.user.get_full_name() or request.user.username}
📧 EMAIL: {request.user.email}
🏭 TIPO NEGOCIO: {request.user.empresa.get_categoria_display()}
📍 UBICACIÓN: {request.user.empresa.ubicacion_completa}
🆔 SOLICITUD: #{solicitud.id}

📋 TIPO DE AYUDA: {solicitud.get_tipo_display()}

💬 MENSAJE:
{mensaje}

---
🔗 RESPONDER DIRECTAMENTE:
http://127.0.0.1:8000/empresa/responder/{solicitud.id}/

📱 O por comando:
python manage.py responder_solicitud --solicitud-id {solicitud.id} --respuesta "Tu respuesta"

---
Solicitud generada automáticamente desde Contafy
            """
            
            # Enviar a tu correo personal
            NotificacionesService.enviar_email(
                'jonathanparedes738@gmail.com',
                email_asunto,
                email_contenido,
                request.user.empresa
            )
            
            # Enviar WhatsApp si está configurado
            whatsapp_mensaje = f"""
NUEVA SOLICITUD CONTAFY

Empresa: {request.user.empresa.nombre}
Usuario: {request.user.username}
Tipo: {solicitud.get_tipo_display()}
ID: #{solicitud.id}

Mensaje: {mensaje[:100]}...

Revisa tu email para detalles completos.
            """.strip()
            
            NotificacionesService.enviar_whatsapp(
                '+593994020346',
                whatsapp_mensaje,
                request.user.empresa
            )
            
            return JsonResponse({
                'success': True, 
                'mensaje': f'Solicitud #{solicitud.id} enviada correctamente. Te responderemos por email.',
                'solicitud_id': solicitud.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al enviar solicitud: {str(e)}'})
    
    # Obtener solicitudes previas del usuario
    solicitudes_recientes = SolicitudAyuda.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')[:3]  # Solo 3 para el panel lateral
    
    solicitudes_bandeja = SolicitudAyuda.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')[:5]  # Solo 5 para la bandeja
    
    return render(request, 'empresa/asistente_ayuda.html', {
        'solicitudes_previas': solicitudes_recientes,
        'solicitudes_bandeja': solicitudes_bandeja
    })

@login_required
def historial_solicitudes(request):
    """Vista para ver historial completo de solicitudes"""
    solicitudes = SolicitudAyuda.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')
    
    return render(request, 'empresa/historial_solicitudes.html', {
        'solicitudes': solicitudes
    })