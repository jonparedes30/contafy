"""
Comando para responder solicitudes por email
"""
from django.core.management.base import BaseCommand
from empresa.models import SolicitudAyuda
from empresa.services.notificaciones_service import NotificacionesService

class Command(BaseCommand):
    help = 'Responde a una solicitud de ayuda por email'

    def add_arguments(self, parser):
        parser.add_argument('--solicitud-id', type=int, help='ID de la solicitud')
        parser.add_argument('--respuesta', type=str, help='Texto de la respuesta')

    def handle(self, *args, **options):
        if not options['solicitud_id']:
            # Mostrar solicitudes pendientes
            solicitudes = SolicitudAyuda.objects.filter(estado='pendiente').order_by('-fecha_creacion')
            
            self.stdout.write('Solicitudes pendientes:')
            for solicitud in solicitudes:
                self.stdout.write(f'ID: {solicitud.id} - {solicitud.asunto} - {solicitud.usuario.username}')
            
            self.stdout.write('\nUso: python manage.py responder_solicitud --solicitud-id 1 --respuesta "Tu respuesta aquí"')
            return
        
        try:
            solicitud = SolicitudAyuda.objects.get(id=options['solicitud_id'])
            respuesta = options['respuesta']
            
            if not respuesta:
                self.stdout.write(f'Solicitud #{solicitud.id}: {solicitud.asunto}')
                self.stdout.write(f'Usuario: {solicitud.usuario.username} ({solicitud.usuario.email})')
                self.stdout.write(f'Mensaje: {solicitud.mensaje}')
                self.stdout.write('\nUsa --respuesta "tu mensaje" para responder')
                return
            
            # Actualizar estado
            solicitud.estado = 'resuelto'
            solicitud.respuesta = respuesta
            solicitud.save()
            
            # Enviar respuesta por email
            email_contenido = f"""
Hola {solicitud.usuario.get_full_name() or solicitud.usuario.username},

Tienes una respuesta a tu solicitud de ayuda en CONTAFY:

SOLICITUD: {solicitud.asunto}
RESPUESTA:
{respuesta}

Si necesitas más ayuda, puedes enviar una nueva solicitud desde tu panel de CONTAFY.

Saludos,
Equipo CONTAFY
            """.strip()
            
            if solicitud.usuario.email:
                resultado = NotificacionesService.enviar_email(
                    solicitud.usuario.email,
                    f'[CONTAFY] Respuesta a tu solicitud: {solicitud.asunto}',
                    email_contenido,
                    solicitud.empresa
                )
                
                if resultado:
                    self.stdout.write(self.style.SUCCESS(f'Respuesta enviada a {solicitud.usuario.email}'))
                else:
                    self.stdout.write(self.style.ERROR('Error enviando email'))
            else:
                self.stdout.write(self.style.WARNING('Usuario no tiene email configurado'))
                
        except SolicitudAyuda.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Solicitud {options["solicitud_id"]} no encontrada'))