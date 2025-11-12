# Despliegue en Render

Estos pasos indican cómo desplegar la aplicación en Render y migrar desde Heroku.

1) Crear cuenta en Render
   - https://render.com

2) Crear servicio web
   - Dashboard → New → Web Service
   - Conectar tu repo GitHub/GitLab
   - Seleccionar `main` (o rama que uses)
   - Build command: dejar vacío si usas Dockerfile
   - Start command: `gunicorn core.wsgi:application --bind 0.0.0.0:8000`
   - Environment: Docker

3) Crear base de datos gestionada
   - Dashboard → Databases → New Database
   - Selecciona Postgres y plan (starter o según carga)
   - Copia la URL (DATABASE_URL)

4) Configurar secretos en el servicio
   - En Settings → Environment → Environment Variables añade:
     - SECRET_KEY
     - DJANGO_SETTINGS_MODULE (ej: heroku_settings_fixed o core.settings de producción)
     - DATABASE_URL (la URL que Te da Render)
     - ADMIN_USERNAME / ADMIN_EMAIL / ADMIN_PASSWORD (opcional)

5) Migraciones y collectstatic
   - En el dashboard puedes usar la sección Shell o ejecutar desde tu máquina:
     - `renderctl` (si lo configuras) o conectar via `heroku pg:pull`-equivalente.
   - Ejecuta:
     - `python manage.py migrate --settings=heroku_settings_fixed`
     - `python manage.py collectstatic --noinput --settings=heroku_settings_fixed`

6) Crear admin automáticamente (opcional)
   - Usa el comando que añadimos:
     - `python manage.py create_admin_from_env --settings=heroku_settings_fixed`
   - Si no quieres crear a mano, configura ADMIN_* env vars y ejecuta el comando desde Shell.

7) Migrar datos desde Heroku (si aplica)
   - En Heroku: `heroku pg:backups:capture -a your-heroku-app`
   - Descargar: `heroku pg:backups:download -a your-heroku-app`
   - Restaurar en Render Postgres con `pg_restore` o mediante la interfaz.

Notas:
- Actualiza `render.yaml` con tu repo real antes de usar render deploy.
- Ajusta `startCommand` según tu WSGI server preferido.
- Revisa variables `ALLOWED_HOSTS` y `SECURE_PROXY_SSL_HEADER` en settings si usas HTTPS.
