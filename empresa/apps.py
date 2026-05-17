import warnings

from django.apps import AppConfig


class EmpresaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'empresa'

    def ready(self):
        import empresa.signals  # noqa: F401

        # ── Warning inmediato si CONN_MAX_AGE es inconsistente ──
        from django.conf import settings
        db = settings.DATABASES.get('default', {})
        engine = db.get('ENGINE', '')
        conn_max_age = db.get('CONN_MAX_AGE', 0)

        if 'sqlite' in engine and conn_max_age > 0:
            warnings.warn(
                f"CONTAFY: CONN_MAX_AGE={conn_max_age} esta configurado "
                f"pero SQLite no soporta connection pooling. "
                f"Establece CONN_MAX_AGE=0 en la configuracion de SQLite.",
                RuntimeWarning,
                stacklevel=2
            )

        # ── Django system checks (se ejecutan con manage.py check) ──
        from django.core.checks import Warning as CheckWarning, register

        @register('database')
        def check_conn_max_age(app_configs, **kwargs):
            """
            Verifica que CONN_MAX_AGE sea coherente con el motor de BD.
            - SQLite: CONN_MAX_AGE debe ser 0 (no soporta connection pooling)
            - PostgreSQL: CONN_MAX_AGE > 0 es recomendado para rendimiento
            """
            check_warnings = []
            db_config = settings.DATABASES.get('default', {})
            db_engine = db_config.get('ENGINE', '')
            db_conn_max_age = db_config.get('CONN_MAX_AGE', 0)

            if 'sqlite' in db_engine and db_conn_max_age > 0:
                check_warnings.append(CheckWarning(
                    f'CONN_MAX_AGE={db_conn_max_age} con SQLite puede causar "database is locked".',
                    hint='Configura CONN_MAX_AGE=0 para SQLite.',
                    id='empresa.W001',
                ))
            elif 'postgresql' in db_engine and db_conn_max_age == 0 and settings.DEBUG:
                check_warnings.append(CheckWarning(
                    'CONN_MAX_AGE=0 con PostgreSQL: cada request abre/cierra conexion.',
                    hint='Configura CONN_MAX_AGE=600 para mejor rendimiento.',
                    id='empresa.W002',
                ))
            return check_warnings
