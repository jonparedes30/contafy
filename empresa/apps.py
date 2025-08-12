from django.apps import AppConfig


class EmpresaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'empresa'
    
    def ready(self):
        # Importar modelos adicionales para que Django los detecte
        try:
            from . import models_aprendizaje
            from . import models_gamificacion  
            from . import models_simulaciones
        except ImportError:
            pass
