$taskName = "ContafyResetDemos"
$batPath  = "C:\Proyectos\contafy\scripts\reset_demos_daily.bat"

# Eliminar tarea previa si existe
schtasks /Delete /TN $taskName /F 2>$null

# Crear la tarea: diaria a las 00:05, para el usuario actual
$result = schtasks /Create `
    /TN $taskName `
    /TR "`"cmd.exe`" /c `"`"$batPath`"`"" `
    /SC DAILY `
    /ST 00:05 `
    /F `
    /RL HIGHEST

Write-Host $result

# Verificar
Write-Host ""
schtasks /Query /TN $taskName /FO LIST

