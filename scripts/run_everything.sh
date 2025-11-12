#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
COMPOSE_FILE="$SCRIPT_DIR/../docker-compose.postgres.yml"

echo "Starting Contafy full-run script..."

if command -v docker >/dev/null 2>&1; then
  echo "Docker found. Running docker compose..."
  if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Compose file not found: $COMPOSE_FILE" >&2
    exit 1
  fi
  docker compose -f "$COMPOSE_FILE" up --build --abort-on-container-exit
  exit $?
else
  echo "Docker not found on PATH. Please install Docker: https://docs.docker.com/get-docker/" >&2
  echo "After installing, re-run:" 
  echo "  bash scripts/run_everything.sh"
  echo "Manual steps (once Docker available):"
  echo "  docker compose -f docker-compose.postgres.yml up -d db redis"
  echo "  export DATABASE_URL='postgres://contafy:contafy@127.0.0.1:5432/contafy_test'"
  echo "  export DJANGO_SETTINGS_MODULE='core.test_settings'"
  echo "  pip install -r requirements-ci.txt"
  echo "  python manage.py migrate --noinput"
  echo "  python manage.py test -v 2"
  exit 2
fi
