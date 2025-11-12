<#
Run full local pipeline for Contafy.

Behavior:
- If Docker is available, runs:
  docker compose -f docker-compose.postgres.yml up --build --abort-on-container-exit

- If Docker is not available, prints instructions to install Docker Desktop and how to run the commands manually.

Usage (PowerShell):
  .\scripts\run_everything.ps1
  # Or if execution policy blocks:
  powershell -ExecutionPolicy Bypass -File .\scripts\run_everything.ps1
#>

function Test-CommandExists {
    param([string]$cmd)
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

Write-Host "Starting Contafy full-run script..." -ForegroundColor Cyan

if (Test-CommandExists docker) {
    Write-Host "Docker detected. Running Docker Compose (Postgres + Redis + web)..." -ForegroundColor Green
    $composeFile = Join-Path $PSScriptRoot "..\docker-compose.postgres.yml"
    if (-not (Test-Path $composeFile)) {
        Write-Error "Compose file not found: $composeFile"
        exit 1
    }

    # Run compose and forward exit code
    docker compose -f $composeFile up --build --abort-on-container-exit
    $exit = $LASTEXITCODE
    if ($exit -eq 0) {
        Write-Host "Compose run finished successfully." -ForegroundColor Green
        exit 0
    } else {
        Write-Error "Compose run exited with code $exit"
        exit $exit
    }
} else {
    Write-Warning "Docker executable not found on PATH."
    Write-Host "Please install Docker Desktop (https://www.docker.com/get-started) and ensure 'docker' is available from PowerShell." -ForegroundColor Yellow
    Write-Host "After installing Docker, re-run this script:" -ForegroundColor Cyan
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\run_everything.ps1" -ForegroundColor White
    Write-Host "If you prefer to run parts manually, here are the commands to run once Docker is available:" -ForegroundColor Cyan
    Write-Host "  docker compose -f docker-compose.postgres.yml up -d db redis" -ForegroundColor White
    Write-Host "  $env:DATABASE_URL='postgres://contafy:contafy@127.0.0.1:5432/contafy_test'`n  $env:DJANGO_SETTINGS_MODULE='core.test_settings'`n  python -m pip install -r requirements-ci.txt`n  python manage.py migrate --noinput`n  python manage.py test -v 2" -ForegroundColor White
    exit 2
}
