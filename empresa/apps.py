from django.apps import AppConfig


class EmpresaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'empresa'
    
    def ready(self):
        import empresa.signals

        # Registrar check de configuración de base de datos
        from django.core.checks import Warning, register

        @register('database')
        def check_conn_max_age(app_configs, **kwargs):
            """
            Verifica que CONN_MAX_AGE sea coherente con el motor de BD.
            - SQLite: CONN_MAX_AGE debe ser 0 (no soporta connection pooling)
            - PostgreSQL: CONN_MAX_AGE > 0 es recomendado para rendimiento
            """
            from django.conf import settings
            warnings = []
            db_config = settings.DATABASES.get('default', {})
            engine = db_config.get('ENGINE', '')
            conn_max_age = db_config.get('CONN_MAX_AGE', 0)

            if 'sqlite' in engine and conn_max_age > 0:
                warnings.append(Warning(
                    f'CONN_MAX_AGE={conn_max_age} con SQLite puede causar "database is locked".',
                    hint='Configura CONN_MAX_AGE=0 para SQLite.',
                    id='empresa.W001',
                ))
            elif 'postgresql' in engine and conn_max_age == 0 and settings.DEBUG:
                warnings.append(Warning(
                    'CONN_MAX_AGE=0 con PostgreSQL: cada request abre/cierra conexión.',
                    hint='Configura CONN_MAX_AGE=600 para mejor rendimiento.',
                    id='empresa.W002',
                ))
            return warnings
