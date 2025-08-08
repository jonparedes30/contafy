"""
Servicio de Notificaciones por Email y WhatsApp
"""
from django.core.mail import send_mail
from django.conf import settings
import requests
import logging
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

class NotificacionesService:
    
    @staticmethod
    def enviar_email(destinatario, asunto, mensaje, empresa=None):
        """Envía notificación por email"""
        try:
            # Usar configuración simple para desarrollo
            from django.core.mail import EmailMessage
            
            email = EmailMessage(
                subject=f"[CONTAFY] {asunto}",
                body=mensaje,
                from_email='jonathanparedes738@gmail.com',
                to=[destinatario],
            )
            email.send()
            
            print(f"Email enviado a {destinatario}: {asunto}")
            return True
        except Exception as e:
            print(f"Error enviando email a {destinatario}: {e}")
            # Mostrar el email en consola como fallback
            print(f"\n--- EMAIL FALLBACK ---")
            print(f"Para: {destinatario}")
            print(f"Asunto: [CONTAFY] {asunto}")
            print(f"Mensaje:\n{mensaje}")
            print(f"--- FIN EMAIL ---\n")
            return False
    
    @staticmethod
    def enviar_whatsapp(telefono, mensaje, empresa=None):
        """Envía notificación por WhatsApp usando API"""
        if not telefono:
            return False
            
        try:
            # Ejemplo con Twilio WhatsApp API
            # Necesitas configurar TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en .env
            
            # Formato del teléfono: +593987654321
            if not telefono.startswith('+'):
                telefono = f"+593{telefono}"
            
            # Por ahora mostrar en consola (WhatsApp requiere configuración adicional)
            print(f"\n--- WHATSAPP MENSAJE ---")
            print(f"Para: {telefono}")
            print(f"Mensaje: {mensaje[:100]}...")
            print(f"--- FIN WHATSAPP ---\n")
            
            # TODO: Configurar Twilio para envío real
            # if hasattr(settings, 'TWILIO_ACCOUNT_SID') and settings.TWILIO_ACCOUNT_SID:
            #     from twilio.rest import Client
            #     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            #     message = client.messages.create(
            #         from_='whatsapp:+14155238886',
            #         body=mensaje,
            #         to=f'whatsapp:{telefono}'
            #     )
            #     print(f"WhatsApp enviado a {telefono}: {message.sid}")
            
            return True
        except Exception as e:
            logger.error(f"Error enviando WhatsApp a {telefono}: {e}")
            return False
    
    @staticmethod
    def notificar_meta_critica(meta):
        """Notifica cuando una meta está en estado crítico"""
        empresa = meta.empresa
        mensaje = f"""
🚨 ALERTA: Meta Crítica

Empresa: {empresa.nombre}
Meta: {meta.get_tipo_display()}
Progreso: {meta.progreso_actual:.1f}%
Objetivo: ${meta.objetivo_mensual:,.2f}
Período: {meta.mes}/{meta.anio}

Tu meta está en riesgo. Revisa tu estrategia urgentemente.

Accede a CONTAFY para más detalles.
        """.strip()
        
        # Enviar a todos los usuarios de la empresa
        for usuario in empresa.usuarios.all():
            if usuario.email:
                NotificacionesService.enviar_email(
                    usuario.email,
                    f"Meta Crítica: {meta.get_tipo_display()}",
                    mensaje,
                    empresa
                )
        
        # Enviar WhatsApp si está configurado
        if empresa.telefono_whatsapp:
            NotificacionesService.enviar_whatsapp(
                empresa.telefono_whatsapp,
                mensaje,
                empresa
            )
    
    @staticmethod
    def notificar_meta_cumplida(meta):
        """Notifica cuando una meta se cumple"""
        empresa = meta.empresa
        mensaje = f"""
🎉 ¡FELICITACIONES!

Empresa: {empresa.nombre}
Meta: {meta.get_tipo_display()}
Progreso: {meta.progreso_actual:.1f}%
Objetivo: ${meta.objetivo_mensual:,.2f}
Período: {meta.mes}/{meta.anio}

¡Has cumplido tu meta! Excelente trabajo.

Revisa tus logros en CONTAFY.
        """.strip()
        
        # Enviar a todos los usuarios de la empresa
        for usuario in empresa.usuarios.all():
            if usuario.email:
                NotificacionesService.enviar_email(
                    usuario.email,
                    f"¡Meta Cumplida!: {meta.get_tipo_display()}",
                    mensaje,
                    empresa
                )
        
        # Enviar WhatsApp si está configurado
        if empresa.telefono_whatsapp:
            NotificacionesService.enviar_whatsapp(
                empresa.telefono_whatsapp,
                mensaje,
                empresa
            )
    
    @staticmethod
    def notificar_stock_bajo(producto):
        """Notifica cuando un producto tiene stock bajo"""
        empresa = producto.empresa
        mensaje = f"""
⚠️ STOCK BAJO

Producto: {producto.nombre}
Código: {producto.codigo}
Stock actual: {producto.stock}
Stock mínimo: {producto.stock_minimo}

Es necesario reabastecer este producto.

Gestiona tu inventario en CONTAFY.
        """.strip()
        
        # Enviar a usuarios con permisos de inventario
        for usuario in empresa.usuarios.all():
            if usuario.email:
                NotificacionesService.enviar_email(
                    usuario.email,
                    f"Stock Bajo: {producto.nombre}",
                    mensaje,
                    empresa
                )
        
        if empresa.telefono_whatsapp:
            NotificacionesService.enviar_whatsapp(
                empresa.telefono_whatsapp,
                mensaje,
                empresa
            )
    
    @staticmethod
    def notificar_alerta_predictiva(empresa, alerta):
        """Notifica alertas del análisis predictivo"""
        mensaje = f"""
🔍 ANÁLISIS PREDICTIVO

Empresa: {empresa.nombre}
Alerta: {alerta['mensaje']}
Prioridad: {alerta['prioridad']}

Recomendación: Revisa tu dashboard financiero para más detalles.

Accede a CONTAFY para análisis completo.
        """.strip()
        
        # Enviar a todos los usuarios de la empresa
        for usuario in empresa.usuarios.all():
            if usuario.email:
                NotificacionesService.enviar_email(
                    usuario.email,
                    f"Alerta Predictiva: {alerta['prioridad']}",
                    mensaje,
                    empresa
                )
        
        if empresa.telefono_whatsapp:
            NotificacionesService.enviar_whatsapp(
                empresa.telefono_whatsapp,
                mensaje,
                empresa
            )