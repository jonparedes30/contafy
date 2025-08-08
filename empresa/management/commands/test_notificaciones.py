"""
Comando para probar el sistema de notificaciones
"""
from django.core.management.base import BaseCommand
from empresa.models import Empresa
from empresa.services.notificaciones_service import NotificacionesService

class Command(BaseCommand):
    help = 'Prueba el sistema de notificaciones'

    def add_arguments(self, parser):
        parser.add_argument('--empresa-id', type=int, help='ID de la empresa')
        parser.add_argument('--email', type=str, help='Email de prueba')
        parser.add_argument('--whatsapp', type=str, help='WhatsApp de prueba')

    def handle(self, *args, **options):
        if options['empresa_id']:
            try:
                empresa = Empresa.objects.get(id=options['empresa_id'])
                
                # Probar email
                if options['email']:
                    resultado_email = NotificacionesService.enviar_email(
                        options['email'],
                        'Prueba de Notificación CONTAFY',
                        f'Esta es una prueba del sistema de notificaciones para {empresa.nombre}.',
                        empresa
                    )
                    if resultado_email:
                        self.stdout.write(self.style.SUCCESS(f'Email enviado a {options["email"]}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'Error enviando email a {options["email"]}'))
                
                # Probar WhatsApp
                if options['whatsapp']:
                    resultado_whatsapp = NotificacionesService.enviar_whatsapp(
                        options['whatsapp'],
                        f'🧪 Prueba CONTAFY\n\nEsta es una prueba del sistema de notificaciones para {empresa.nombre}.\n\n¡El sistema funciona correctamente!',
                        empresa
                    )
                    if resultado_whatsapp:
                        self.stdout.write(self.style.SUCCESS(f'WhatsApp enviado a {options["whatsapp"]}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'Error enviando WhatsApp a {options["whatsapp"]}'))
                
                # Si no se especifica email ni WhatsApp, usar los de la empresa
                if not options['email'] and not options['whatsapp']:
                    # Probar con usuarios de la empresa
                    for usuario in empresa.usuarios.all():
                        if usuario.email:
                            NotificacionesService.enviar_email(
                                usuario.email,
                                'Prueba Sistema CONTAFY',
                                f'Hola {usuario.username},\n\nEsta es una prueba del sistema de notificaciones.\n\nSaludos,\nEquipo CONTAFY',
                                empresa
                            )
                            self.stdout.write(f'Email enviado a {usuario.email}')
                    
                    # Probar WhatsApp de la empresa
                    if empresa.telefono_whatsapp:
                        NotificacionesService.enviar_whatsapp(
                            empresa.telefono_whatsapp,
                            f'🧪 Prueba CONTAFY\n\nSistema de notificaciones funcionando correctamente para {empresa.nombre}.',
                            empresa
                        )
                        self.stdout.write(f'WhatsApp enviado a {empresa.telefono_whatsapp}')
                    else:
                        self.stdout.write(self.style.WARNING('No hay WhatsApp configurado para la empresa'))
                        
            except Empresa.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Empresa con ID {options["empresa_id"]} no encontrada'))
        else:
            self.stdout.write('Uso: python manage.py test_notificaciones --empresa-id 1 [--email test@email.com] [--whatsapp +593987654321]')