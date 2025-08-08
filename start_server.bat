@echo off
cd /d "c:\Proyectos\contafy"
set DJANGO_SETTINGS_MODULE=core.settings
python manage.py runserver 127.0.0.1:8000
pause