"""
Configuración optimizada para desarrollo local
Usar con: python manage.py runserver --settings=core.dev_settings
"""
from .settings import *

# Desactivar características costosas en desarrollo
DEBUG = True

# Logging mínimo
LOGGING['handlers']['console']['level'] = 'ERROR'
LOGGING['root']['level'] = 'ERROR'

# Caché más agresivo
CACHES['default']['TIMEOUT'] = 3600  # 1 hora

# Desactivar algunos middlewares pesados en desarrollo
MIDDLEWARE = [m for m in MIDDLEWARE if 'SecurityMiddleware' not in m]

# Template caching
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

print("🚀 Usando configuración optimizada para desarrollo")
