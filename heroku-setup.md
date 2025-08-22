# Configuración para Heroku

## Variables de entorno requeridas:

```bash
heroku config:set DEBUG=False
heroku config:set SECRET_KEY="tu-secret-key-super-segura-aqui"
heroku config:set ALLOWED_HOSTS="tu-app.herokuapp.com,.herokuapp.com"
heroku config:set DATABASE_URL="postgres://..."
```

## Comandos de despliegue:

```bash
# 1. Crear app en Heroku
heroku create tu-app-name

# 2. Agregar addon de PostgreSQL
heroku addons:create heroku-postgresql:mini

# 3. Configurar variables de entorno
heroku config:set DEBUG=False
heroku config:set SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
heroku config:set ALLOWED_HOSTS="tu-app.herokuapp.com,.herokuapp.com"

# 4. Desplegar
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# 5. Ejecutar migraciones
heroku run python manage.py migrate

# 6. Crear superusuario
heroku run python manage.py createsuperuser

# 7. Recopilar archivos estáticos
heroku run python manage.py collectstatic --noinput
```

## Verificar logs:
```bash
heroku logs --tail
```