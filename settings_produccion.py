import os
import dj_database_url
from .settings import *

# Configuración para producción
DEBUG = False
ALLOWED_HOSTS = ['contafy-pruebas.herokuapp.com', 'localhost', '127.0.0.1']

# Base de datos para producción
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'))
}

# Archivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware para archivos estáticos
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# CORS para PWA
CORS_ALLOWED_ORIGINS = [
    "https://contafy-pruebas.herokuapp.com",
]

# Seguridad HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')