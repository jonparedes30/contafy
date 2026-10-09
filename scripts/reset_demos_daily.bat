@echo off
REM ============================================================
REM  CONTAFY — Reset diario de transacciones demo
REM  Se ejecuta automáticamente cada noche via Task Scheduler.
REM  Protege datos anteriores a 2026-05-22.
REM ============================================================

cd /d C:\Proyectos\contafy

REM Registrar hora de inicio en el log
echo. >> logs\reset_demos.log
echo ===== %DATE% %TIME% ===== >> logs\reset_demos.log

REM Activar entorno virtual y correr el reset
call venv\Scripts\activate.bat
python manage.py reset_demos >> logs\reset_demos.log 2>&1

REM Salir limpiamente
exit /b 0
