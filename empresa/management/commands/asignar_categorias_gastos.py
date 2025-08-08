from django.core.management.base import BaseCommand
from empresa.models import Gasto
from empresa.services.categorizador import categorizar_gastos_queryset

class Command(BaseCommand):
    help = 'Asigna categorías por defecto a gastos existentes'

    def handle(self, *args, **options):
        gastos = Gasto.objects.all()
        resumen = categorizar_gastos_queryset(gastos)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Categorización completada:\n'
                f'   Total gastos: {resumen["total"]}\n'
                f'   Gastos fijos: {resumen["fijos"]}\n'
                f'   Gastos variables: {resumen["variables"]}\n'
                f'   Sin cambio: {resumen["sin_cambio"]}'
            )
        ) 