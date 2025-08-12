from django.core.management.base import BaseCommand
from empresa.models_gamificacion import Logro, Insignia

class Command(BaseCommand):
    help = 'Crea los logros e insignias iniciales'

    def handle(self, *args, **options):
        # Limpiar datos existentes
        Logro.objects.all().delete()
        Insignia.objects.all().delete()
        
        # LOGROS GENERALES
        logros = [
            {
                'nombre': 'Primer Paso',
                'descripcion': 'Completa tu primera lección',
                'icono': 'fas fa-baby',
                'tipo': 'primera_vez',
                'condicion_valor': 1,
                'puntos_xp_premio': 25
            },
            {
                'nombre': 'Estudiante Dedicado',
                'descripcion': 'Acumula 100 puntos de experiencia',
                'icono': 'fas fa-book-open',
                'tipo': 'puntos_xp',
                'condicion_valor': 100,
                'puntos_xp_premio': 50
            },
            {
                'nombre': 'Experto en Formación',
                'descripcion': 'Acumula 500 puntos de experiencia',
                'icono': 'fas fa-graduation-cap',
                'tipo': 'puntos_xp',
                'condicion_valor': 500,
                'puntos_xp_premio': 100
            },
            {
                'nombre': 'Maestro Contable',
                'descripcion': 'Acumula 1000 puntos de experiencia',
                'icono': 'fas fa-crown',
                'tipo': 'puntos_xp',
                'condicion_valor': 1000,
                'puntos_xp_premio': 200
            },
            {
                'nombre': 'Constancia',
                'descripción': 'Mantén una racha de 3 días consecutivos',
                'icono': 'fas fa-fire',
                'tipo': 'racha_dias',
                'condicion_valor': 3,
                'puntos_xp_premio': 75
            },
            {
                'nombre': 'Disciplina',
                'descripcion': 'Mantén una racha de 7 días consecutivos',
                'icono': 'fas fa-medal',
                'tipo': 'racha_dias',
                'condicion_valor': 7,
                'puntos_xp_premio': 150
            },
            {
                'nombre': 'Completista',
                'descripcion': 'Completa tu primer módulo completo',
                'icono': 'fas fa-check-circle',
                'tipo': 'completar_modulo',
                'condicion_valor': 1,
                'puntos_xp_premio': 100
            }
        ]
        
        for logro_data in logros:
            Logro.objects.create(**logro_data)
        
        # INSIGNIAS POR CATEGORÍA
        insignias = [
            {
                'nombre': 'Comerciante Novato',
                'descripcion': 'Domina los fundamentos del comercio',
                'icono': 'fas fa-store',
                'categoria': 'comercial',
                'color': '#28a745',
                'requisito_xp': 100
            },
            {
                'nombre': 'Comerciante Experto',
                'descripcion': 'Experto en gestión comercial',
                'icono': 'fas fa-chart-line',
                'categoria': 'comercial',
                'color': '#ffc107',
                'requisito_xp': 500
            },
            {
                'nombre': 'Productor Novato',
                'descripcion': 'Domina los fundamentos de manufactura',
                'icono': 'fas fa-industry',
                'categoria': 'manufactura',
                'color': '#17a2b8',
                'requisito_xp': 100
            },
            {
                'nombre': 'Productor Experto',
                'descripcion': 'Experto en procesos de manufactura',
                'icono': 'fas fa-cogs',
                'categoria': 'manufactura',
                'color': '#6f42c1',
                'requisito_xp': 500
            },
            {
                'nombre': 'Prestador Novato',
                'descripcion': 'Domina los fundamentos de servicios',
                'icono': 'fas fa-handshake',
                'categoria': 'servicios',
                'color': '#fd7e14',
                'requisito_xp': 100
            },
            {
                'nombre': 'Prestador Experto',
                'descripcion': 'Experto en gestión de servicios',
                'icono': 'fas fa-user-tie',
                'categoria': 'servicios',
                'color': '#e83e8c',
                'requisito_xp': 500
            }
        ]
        
        for insignia_data in insignias:
            Insignia.objects.create(**insignia_data)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Creados {len(logros)} logros y {len(insignias)} insignias')
        )