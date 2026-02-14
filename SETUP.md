# SETUP - CONTAFY Development & Docker

**Estado**: ✅ Production-Ready (Nivel 4)  
**Última actualización**: 2026-02-13  
**Entorno**: Python 3.11 | Django 5.2.3 | PostgreSQL 15

---

## 🚀 Quick Start (5 minutos)

### Opción A: Docker (Recomendado)

```bash
git clone <repo> && cd contafy
cp .env.example .env
docker compose up --build
```

Acceder: http://localhost:8000

### Opción B: Local Python (Sin Docker)

```bash
git clone <repo> && cd contafy
python -m venv .venv
source .venv/bin/activate  # Linux/Mac o .venv\Scripts\activate (Windows)
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Acceder: http://localhost:8000

---

## 🐳 Docker Completo

### Requisitos
- Docker Desktop instalado
- 2GB RAM mínimo

### Levantar

```bash
docker compose up --build
```

**Automático**:
- ✅ PostgreSQL 15
- ✅ Django + Gunicorn
- ✅ Migraciones aplicadas
- ✅ Archivos estáticos
- ✅ Health checks

### Verificar

```bash
# Logs en tiempo real
docker compose logs -f web

# Ver estado
docker compose ps

# Shell Django
docker compose exec web python manage.py shell

# Crear superuser
docker compose exec web python manage.py createsuperuser
```

### Parar

```bash
docker compose down       # Mantiene datos
docker compose down -v    # Elimina datos (limpia todo)
```

---

## 📝 Archivo .env

### Desarrollo Local (SQLite)
```
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=dev-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=  # ← vacío para SQLite
```

### Docker (PostgreSQL)
```
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=dev-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,127.0.0.1:8000
POSTGRES_DB=contafy_db
POSTGRES_USER=contafy
POSTGRES_PASSWORD=changeme
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### Producción
```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<secreto-largo-50+chars>
ALLOWED_HOSTS=mi-dominio.com,www.mi-dominio.com
DATABASE_URL=postgres://...
LOG_LEVEL=INFO
```

---

## 🔍 Validación Post-Setup

```bash
# Verificar Django
docker compose exec web python manage.py check

# Ver migraciones
docker compose exec web python manage.py showmigrations empresa

# Contar tablas BD
docker compose exec web python manage.py shell
>>> from django.db import connection
>>> print(f"{len(connection.introspection.table_names())} tablas")

# Acceder admin
# http://localhost:8000/admin
```

---

## 🚨 Troubleshooting

| Problema | Solución |
|----------|----------|
| "Connection refused" | `docker compose down && docker compose up` (espera 10s) |
| "database doesn't exist" | `docker compose exec web python manage.py migrate` |
| "Port 5432 in use" | Cambiar en docker-compose.yml "5432:5432" → "5433:5432" |
| "permission denied" | `docker compose exec web chown -R app:app /app` |
| Limpiar todo | `docker compose down -v && docker system prune -a` |

---

## 📦 Estructura

```
contafy/
├── core/settings.py          # ✅ Endurecido (Level 4)
├── empresa/migrations/        # ✅ Reparadas (Level 3)
├── Dockerfile                 # ✅ Multi-stage
├── docker-compose.yml         # ✅ Production-grade
├── .env.example              # Template
├── requirements.txt          # Dependencias fijas
└── manage.py
```

---

## 🔐 Seguridad

**Dev**: DEBUG=True, SQLite, SECRET_KEY simple  
**Prod**: DEBUG=False, PostgreSQL, SECRET_KEY 50+, HTTPS, HSTS

---

**Last Update**: 2026-02-13  
**Status**: ✅ Production-Ready

