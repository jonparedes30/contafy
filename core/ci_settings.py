# CI Settings for PostgreSQL testing
from .settings import *  # importa configuración base

import os

# Intentar usar dj-database-url si está disponible (comodidad en CI)
try:
    import dj_database_url  # optional dependency
except Exception:
    dj_database_url = None

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and dj_database_url:
    DATABASES["default"] = dj_database_url.parse(DATABASE_URL, conn_max_age=600)  # type: ignore[assignment]
else:
    # fallback a variables individuales (servicio postgres en CI)
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "contafy_test"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }

# valores seguros para CI
SECRET_KEY = os.getenv("SECRET_KEY", "ci-secret-key")
DEBUG = False
ALLOWED_HOSTS = ["*"]

# reducir ruido de logging en CI
if "LOGGING" in globals():
    LOGGING["loggers"].setdefault("django", {})["level"] = "ERROR"