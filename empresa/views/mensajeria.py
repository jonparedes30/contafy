from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from empresa.models import ConversacionSoporte, MensajeSoporte
from empresa.services.notificaciones_service import NotificacionesService
import json

@login_required
def bandeja_entrada(request):
    """Vista de bandeja de entrada del usuario"""
    conversaciones = ConversacionSoporte.objects.filter(
        usuario=request.user
    ).prefetch_related('mensajes')
    
    return render(request, 'empresa/bandeja_entrada.html', {
        'conversaciones': conversaciones
    })

@login_required
def ver_conversacion(request, conversacion_id):
    """Vista para ver una conversación específica"""
    conversacion = get_object_or_404(
        ConversacionSoporte, 
        id=conversacion_id, 
        usuario=request.user
    )
    
    # Marcar mensajes de soporte como leídos
    MensajeSoporte.objects.filter(
        conversacion=conversacion,
        tipo='soporte',
        leido=False
    ).update(leido=True)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mensaje_texto = data.get('mensaje', '').strip()
            
            if mensaje_texto:
                # Crear nuevo mensaje del usuario
                MensajeSoporte.objects.create(
                    conversacion=conversacion,
                    tipo='usuario',
                    mensaje=mensaje_texto
                )
                
                # Actualizar fecha de conversación
                conversacion.save()
                
                # Notificar por email
                email_contenido = f"""
Nueva respuesta en conversación #{conversacion.id}

Empresa: {conversacion.empresa.nombre}
Usuario: {conversacion.usuario.username}
Solicitud: {conversacion.solicitud_ayuda.asunto}

Mensaje:
{mensaje_texto}

---
Responde desde el panel de administración de CONTAFY
                """.strip()
                
                NotificacionesService.enviar_email(
                    'jonathanparedes738@gmail.com',
                    f'[CONTAFY] Nueva respuesta - Conversación #{conversacion.id}',
                    email_contenido,
                    conversacion.empresa
                )
                
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Mensaje enviado correctamente'
                })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al enviar mensaje: {str(e)}'
            })
    
    return render(request, 'empresa/conversacion.html', {
        'conversacion': conversacion
    })

def responder_conversacion(request, conversacion_id):
    """Vista para que el administrador responda (acceso directo por URL)"""
    if request.method == 'POST':
        try:
            conversacion = get_object_or_404(ConversacionSoporte, id=conversacion_id)
            mensaje_texto = request.POST.get('mensaje', '').strip()
            
            if mensaje_texto:
                # Crear mensaje de soporte
                MensajeSoporte.objects.create(
                    conversacion=conversacion,
                    tipo='soporte',
                    mensaje=mensaje_texto
                )
                
                # Actualizar conversación
                conversacion.save()
                
                # Notificar al usuario por email
                email_contenido = f"""
Hola {conversacion.usuario.get_full_name() or conversacion.usuario.username},

Tienes una nueva respuesta de soporte en CONTAFY:

{mensaje_texto}

Puedes ver la conversación completa ingresando a tu cuenta en CONTAFY > Asistente > Bandeja de Entrada.

Saludos,
Equipo CONTAFY
                """.strip()
                
                if conversacion.usuario.email:
                    NotificacionesService.enviar_email(
                        conversacion.usuario.email,
                        f'[CONTAFY] Nueva respuesta de soporte',
                        email_contenido,
                        conversacion.empresa
                    )
                
                messages.success(request, 'Respuesta enviada correctamente')
                return redirect('empresa:responder_conversacion', conversacion_id=conversacion_id)
        
        except Exception as e:
            messages.error(request, f'Error al enviar respuesta: {str(e)}')
    
    conversacion = get_object_or_404(ConversacionSoporte, id=conversacion_id)
    return render(request, 'empresa/admin_conversacion.html', {
        'conversacion': conversacion
    })