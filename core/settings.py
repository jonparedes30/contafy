import environ
from datetime import timedelta
from pathlib import Path
import os
import secrets



BASE_DIR = Path(__file__).resolve().parent.parent

# Inicializar entorno
env = environ.Env(
    DEBUG=(bool, False),
    LOG_LEVEL=(str, 'INFO')
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

DEBUG = env('DEBUG')
SECRET_KEY = env('SECRET_KEY')
if not SECRET_KEY or SECRET_KEY == 'clave_de_prueba_contafy':
    raise ValueError("SECRET_KEY debe ser configurada en .env")

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '.herokuapp.com'])

# Configuración de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Aplicaciones instaladas
INSTALLED_APPS = [
    'jazzmin',  # Tema profesional para el admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # Django REST Framework
    'rest_framework.authtoken',  # Autenticación por token
    'empresa',  # Tu app principal
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'empresa.middleware.CurrentUserMiddleware',
    'empresa.middleware.SecurityMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Puedes agregar rutas a plantillas aquí si usas una carpeta común
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'empresa.context_processors.breadcrumbs',  # Breadcrumbs processor
                'empresa.context_processors.user_permissions',  # User permissions processor
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Base de datos: Postgres en producción, SQLite en desarrollo
DATABASE_URL = env('DATABASE_URL', default=None)
if DATABASE_URL:
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }
    DATABASES['default']['CONN_MAX_AGE'] = env.int('CONN_MAX_AGE', default=600)
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'contafy_sistema.db',
            'OPTIONS': {
                'timeout': 20,
                'check_same_thread': False,
            },
        }
    }

DATABASES['default']['ATOMIC_REQUESTS'] = True

# Configuración de caché
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'contafy-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Configuración regional
LANGUAGE_CODE = 'es'  # Puedes cambiar a 'en-us' si prefieres inglés
TIME_ZONE = 'America/Guayaquil'  # Zona horaria de Ecuador
USE_I18N = True
USE_TZ = True

# Configuración de moneda global - DÓLARES USD
CURRENCY_SYMBOL = '$'
CURRENCY_CODE = 'USD'
CURRENCY_NAME = 'Dólares Americanos'

# Archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Storage para estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Usuario personalizado
AUTH_USER_MODEL = 'empresa.Usuario'

# URLs de login y logout
LOGIN_URL = '/app-beta-2024/login/'
LOGIN_REDIRECT_URL = '/app-beta-2024/home/'
LOGOUT_REDIRECT_URL = '/app-beta-2024/login/'

# --- CSRF para desarrollo local y Heroku ---
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.herokuapp.com',
]

# Configuración para proxy de Heroku
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_TZ = True

# Configuración de Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# Configuración de Email - Siempre usar SMTP real
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@contafy.com')

# Configuración de WhatsApp (Twilio)
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')

# Configuración de APIs de IA
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')

# Configuración de logging simplificada para Heroku
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'empresa': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
