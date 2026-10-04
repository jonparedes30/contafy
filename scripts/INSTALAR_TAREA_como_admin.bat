@echo off
REM ============================================================
REM  CONTAFY — Registrar tarea de reset diario de demos
REM  Ejecuta este archivo como Administrador (clic derecho → Ejecutar como administrador)
REM ============================================================

echo Registrando tarea programada "ContafyResetDemos"...

schtasks /Delete /TN "ContafyResetDemos" /F 2>nul

schtasks /Create ^
  /TN "ContafyResetDemos" ^
  /TR "\"C:\Proyectos\contafy\scripts\reset_demos_daily.bat\"" ^
  /SC DAILY ^
  /ST 00:05 ^
  /RL HIGHEST ^
  /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo === Tarea registrada exitosamente ===
    schtasks /Query /TN "ContafyResetDemos" /FO LIST
) else (
    echo.
    echo ERROR: No se pudo registrar la tarea.
    echo Asegurate de ejecutar este archivo como Administrador.
)

pause
