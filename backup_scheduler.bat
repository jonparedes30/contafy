@echo off
REM Script para programar respaldos automáticos en Windows
REM Ejecutar como administrador

echo Configurando respaldos automáticos para CONTAFY...

REM Crear tarea programada para respaldo diario a las 2:00 AM
schtasks /create /tn "CONTAFY_Backup_Daily" /tr "cd /d %~dp0 && python manage.py backup_database" /sc daily /st 02:00 /f

REM Crear tarea programada para limpieza semanal de respaldos antiguos
schtasks /create /tn "CONTAFY_Cleanup_Weekly" /tr "cd /d %~dp0 && python backup_manager.py" /sc weekly /d SUN /st 03:00 /f

echo ✅ Respaldos automáticos configurados exitosamente
echo - Respaldo diario: 2:00 AM
echo - Limpieza semanal: Domingos 3:00 AM
pause