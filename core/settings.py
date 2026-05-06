import environ
from datetime import timedelta
from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

# Inicializar entorno
env = environ.Env(
    DEBUG=(bool, False),
    LOG_LEVEL=(str, 'INFO'),
    ENVIRONMENT=(str, 'development'),
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Detectar entorno
ENVIRONMENT = env('ENVIRONMENT')  # development, staging, production
IS_PRODUCTION = ENVIRONMENT == 'production'
DEBUG = env('DEBUG') and not IS_PRODUCTION

# SECRET_KEY: OBLIGATORIO en producción
SECRET_KEY = env('SECRET_KEY', default='')  # type: ignore[arg-type]
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise ValueError('✗ SECRET_KEY OBLIGATORIO en producción. Configura en .env')
    # En desarrollo, generar temporalmente
    SECRET_KEY = 'dev-key-only-for-local'

# ALLOWED_HOSTS: desde entorno
ALLOWED_HOSTS_STR = str(env('ALLOWED_HOSTS', default='localhost,127.0.0.1,*'))  # type: ignore[arg-type]
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_STR.split(',')]
if IS_PRODUCTION and '*' in ALLOWED_HOSTS:
    raise ValueError('✗ ALLOWED_HOSTS no puede ser * en producción')

# Detectar plataformas de hosting
IS_RENDER = 'RENDER' in os.environ or 'RAILWAY_ENVIRONMENT' in os.environ
IS_DOCKER = 'DOCKER_RUNNING' in os.environ

# Configuración de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CSRF configuración estricta en PROD
CSRF_COOKIE_SECURE = IS_PRODUCTION or IS_RENDER
CSRF_COOKIE_SAMESITE = 'Strict' if IS_PRODUCTION else 'Lax'
CSRF_COOKIE_HTTPONLY = True  # Siempre True por seguridad
CSRF_COOKIE_AGE = 31449600  # 1 año
CSRF_USE_SESSIONS = False
CSRF_COOKIE_NAME = 'csrftoken'

# CSRF_TRUSTED_ORIGINS desde entorno
CSRF_TRUSTED_ORIGINS_STR = str(env('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000'))  # type: ignore[arg-type]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in CSRF_TRUSTED_ORIGINS_STR.split(',')]

# Agregar RENDER_EXTERNAL_URL si existe
render_url = os.environ.get('RENDER_EXTERNAL_URL', '')
if render_url and render_url not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(render_url)

# SESSION configuración segura
SESSION_COOKIE_SECURE = IS_PRODUCTION or IS_RENDER
SESSION_COOKIE_SAMESITE = 'Strict' if IS_PRODUCTION else 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400 * 7  # 7 días

# HSTS solo en PROD
SECURE_HSTS_SECONDS = 31536000 if IS_PRODUCTION else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = IS_PRODUCTION
SECURE_HSTS_PRELOAD = IS_PRODUCTION

# SSL Redirect
SECURE_SSL_REDIRECT = IS_PRODUCTION or IS_RENDER
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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
    # WhiteNoise se añade condicionalmente más abajo si está instalado
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'empresa.middleware.CurrentUserMiddleware',
    'empresa.middleware.EmpresaValidationMiddleware',
    'empresa.middleware.SecurityMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Puedes agregar rutas a plantillas aquí si usas una carpeta común
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
DATABASE_URL = env('DATABASE_URL', default='')  # type: ignore[arg-type]

if DATABASE_URL:
    # Usar DATABASE_URL si está configurado (para Render, Heroku, etc)
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,  # type: ignore[arg-type]
            conn_max_age=env.int('CONN_MAX_AGE', default=600),  # type: ignore[arg-type]
            conn_health_checks=True,
        )
    }
elif IS_DOCKER or IS_PRODUCTION:
    # Configuración explícita de PostgreSQL (para Docker y producción)
    POSTGRES_DB = env('POSTGRES_DB', default='contafy_db')  # type: ignore[arg-type]
    POSTGRES_USER = env('POSTGRES_USER', default='postgres')  # type: ignore[arg-type]
    POSTGRES_PASSWORD = env('POSTGRES_PASSWORD', default='')  # type: ignore[arg-type]
    POSTGRES_HOST = env('POSTGRES_HOST', default='localhost')  # type: ignore[arg-type]
    POSTGRES_PORT = env.int('POSTGRES_PORT', default=5432)  # type: ignore[arg-type]
    
    if IS_PRODUCTION and not POSTGRES_PASSWORD:
        raise ValueError('✗ POSTGRES_PASSWORD es OBLIGATORIO en producción')
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': POSTGRES_DB,
            'USER': POSTGRES_USER,
            'PASSWORD': POSTGRES_PASSWORD,
            'HOST': POSTGRES_HOST,
            'PORT': POSTGRES_PORT,
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': {
                'sslmode': 'require' if IS_PRODUCTION else 'disable',
            }
        }
    }
else:
    # SQLite para desarrollo local
    # CONN_MAX_AGE=0: SQLite no soporta connection pooling, mantener en 0
    # para evitar errores "database is locked" por conexiones persistentes.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'contafy_sistema.db',
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': 0,
            'OPTIONS': {
                'timeout': 20,
                'check_same_thread': False,
            },
        }
    }

# Configuración de respaldos automáticos
BACKUP_ENABLED = env.bool('BACKUP_ENABLED', default=True)  # type: ignore[arg-type]
BACKUP_RETENTION_DAYS = env.int('BACKUP_RETENTION_DAYS', default=30)  # type: ignore[arg-type]
BACKUP_SCHEDULE = env('BACKUP_SCHEDULE', default='daily')  # type: ignore[arg-type]  # daily, weekly, monthly

# Configuración de caché
# Usa Redis si REDIS_URL está definido, LocMemCache como fallback para desarrollo local
REDIS_URL = env('REDIS_URL', default='')  # type: ignore[arg-type]

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'TIMEOUT': 300,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'RETRY_ON_TIMEOUT': True,
                'MAX_CONNECTIONS': 50,
            },
            'KEY_PREFIX': 'contafy',
        }
    }
    # Usar Redis como backend de sesiones cuando está disponible
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
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

# Google Vision API key (se recomienda configurar en entorno; aquí queda un
# valor por defecto temporal si no se configura la variable de entorno).
GOOGLE_VISION_API_KEY = env('GOOGLE_VISION_API_KEY', default='AIzaSyDD4cb3ZQPtnl30MQxv_Pvs1TmM6O-3yE4')  # provided by user

# Storage para estáticos (usar WhiteNoise si está instalado)
try:
    import importlib.util
    if importlib.util.find_spec('whitenoise'):
        # Insertar WhiteNoise justo después de SecurityMiddleware
        MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
        STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
except Exception:
    # Entornos de prueba/minimos pueden no tener whitenoise instalado
    pass

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Usuario personalizado
AUTH_USER_MODEL = 'empresa.Usuario'

# URLs de login y logout
LOGIN_URL = '/app-beta-2024/login/'
LOGIN_REDIRECT_URL = '/app-beta-2024/home/'
LOGOUT_REDIRECT_URL = '/app-beta-2024/login/'

# --- CSRF para desarrollo local, Heroku y Render ---
# Ya configurado arriba en la sección de seguridad

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
    
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')  # type: ignore[arg-type]
EMAIL_PORT = env.int('EMAIL_PORT', default=587)  # type: ignore[arg-type]
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)  # type: ignore[arg-type]
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')  # type: ignore[arg-type]
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')  # type: ignore[arg-type]
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@contafy.com')  # type: ignore[arg-type]

# Configuración de WhatsApp (Twilio)
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')  # type: ignore[arg-type]
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')  # type: ignore[arg-type]

# Configuración de APIs de IA
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')  # type: ignore[arg-type]
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')  # type: ignore[arg-type]

# Proveedor de IA: 'openai', 'gemini', 'mock' (para tests sin API keys)
AI_PROVIDER = env('AI_PROVIDER', default='gemini')  # type: ignore[arg-type]

# Configuración de sesiones persistentes
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Configuración de logging production-grade
LOG_LEVEL = env('LOG_LEVEL', default='INFO' if IS_PRODUCTION else 'DEBUG')  # type: ignore[arg-type]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['null'],  # Desactivar logs de SQL en verbose
            'level': 'DEBUG',
            'propagate': False,
        },
        'empresa': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'rest_framework': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
