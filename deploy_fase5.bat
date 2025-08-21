@echo off
echo Desplegando Fase 5 y optimizaciones móviles a Heroku...

echo.
echo 1. Haciendo commit de cambios...
git add .
git commit -m "Fase 5 Academia + Optimizaciones móviles"

echo.
echo 2. Desplegando a Heroku...
git push heroku main

echo.
echo 3. Aplicando migraciones...
heroku run python manage.py migrate

echo.
echo 4. Recolectando archivos estáticos...
heroku run python manage.py collectstatic --noinput

echo.
echo 5. Creando liga semanal...
heroku run python manage.py crear_liga_semanal

echo.
echo ✅ Despliegue completado!
echo.
echo URLs disponibles:
echo - Academia: /empresa/aprendizaje/
echo - Social: /empresa/aprendizaje/social/
echo.
pause