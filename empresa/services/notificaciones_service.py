"""Servicio de Notificaciones por Email y WhatsApp con protecciones para modo sandbox.

Este módulo evita enviar emails o llamadas externas cuando `empresa.sandbox_mode.is_sandbox()` está activo.
También centraliza logging y maneja fallbacks seguros (imprimir en consola).
"""
import logging
from django.conf import settings
from django.core.mail import EmailMessage
from empresa.sandbox_mode import is_sandbox

logger = logging.getLogger(__name__)


class NotificacionesService:

    @staticmethod
    def enviar_email(destinatario, asunto, mensaje, empresa=None):
        """Envía notificación por email.

        Retorna True si el envío se realizó o fue omitido por sandbox. Never raises.
        """
        try:
            # No enviar emails en modo sandbox
            if is_sandbox():
                logger.info(f"[SANDBOX] Skipping email to {destinatario}: {asunto}")
                return True

            email = EmailMessage(
                subject=f"[CONTAFY] {asunto}",
                body=mensaje,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@contafy.local'),
                to=[destinatario],
            )
            email.send(fail_silently=False)
            logger.info(f"Email sent to {destinatario}: {asunto}")
            return True
        except Exception as e:
            # Log the failure and fallback to console output
            logger.exception(f"Error sending email to {destinatario}: {e}")
            try:
                print(f"\n--- EMAIL FALLBACK ---")
                print(f"Para: {destinatario}")
                print(f"Asunto: [CONTAFY] {asunto}")
                print(f"Mensaje:\n{mensaje}")
                print(f"--- FIN EMAIL ---\n")
            except Exception:
                logger.exception("Failed to print email fallback")
            return False

    @staticmethod
    def enviar_whatsapp(telefono, mensaje, empresa=None):
        """Envía notificación por WhatsApp (simulado si no está configurado).

        Returns True if message would have been sent or was skipped due to sandbox.
        """
        if not telefono:
            return False

        try:
            if is_sandbox():
                logger.info(f"[SANDBOX] Skipping WhatsApp to {telefono}")
                return True

            # Normalize phone (best-effort)
            if not telefono.startswith('+'):
                telefono = f"+593{telefono}"

            # If Twilio is configured use it, otherwise print to console
            if getattr(settings, 'TWILIO_ACCOUNT_SID', None):
                try:
                    # Import dynamico para evitar errores si la librería no está instalada
                    import importlib
                    twilio_mod = importlib.import_module('twilio.rest') if importlib.util.find_spec('twilio.rest') else None
                    Client = getattr(twilio_mod, 'Client', None) if twilio_mod else None
                    if Client:
                        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                        message = client.messages.create(
                            from_='whatsapp:+14155238886',
                            body=mensaje,
                            to=f'whatsapp:{telefono}'
                        )
                        logger.info(f"WhatsApp sent to {telefono}: {getattr(message, 'sid', '')}")
                        return True
                except Exception:
                    logger.exception("Twilio send failed, falling back to console")

            # Fallback: print message
            print(f"\n--- WHATSAPP MESSAGE ---")
            print(f"Para: {telefono}")
            print(f"Mensaje: {mensaje[:400]}")
            print(f"--- END WHATSAPP ---\n")
            return True
        except Exception as e:
            logger.exception(f"Error preparing WhatsApp to {telefono}: {e}")
            return False

    # The higher-level notification methods keep using enviar_email/enviar_whatsapp
    # and therefore automatically respect sandbox mode.