from django.core.management.base import BaseCommand
from empresa.services.social_service import SocialService

class Command(BaseCommand):
    help = 'Crea una nueva liga semanal automáticamente'

    def handle(self, *args, **options):
        liga = SocialService.crear_liga_semanal()
        
        if liga:
            participantes_count = liga.participantes.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Liga "{liga.nombre}" creada exitosamente con {participantes_count} participantes'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('La liga semanal ya existe para esta semana')
            )