# PRODUCCION - Checklist de Deployment

**Fecha**: 2026-02-13  
**Status**: ✅ NIVEL 4 READY  
**Destinatario**: DevOps/SRE/Tech Lead

---

## 🎯 Este documento te guía paso a paso para llevar CONTAFY a producción.

---

## 📋 Pre-Deployment Checklist

### ✅ Código
- [ ] `git push origin main` - cambios commiteados
- [ ] No hay pendientes con `git status`
- [ ] No hay secretos en código (grep `SECRET_KEY`, `PASSWORD`, etc)
- [ ] `DEBUG=False` en settings

### ✅ Variables de Entorno
- [ ] `ENVIRONMENT=production` configurado
- [ ] `SECRET_KEY` es una cadena aleatoria de 50+ caracteres
- [ ] `ALLOWED_HOSTS` = dominios específicos (NO `*`)
- [ ] `DATABASE_URL` apunta a BD PostgreSQL remota
- [ ] `POSTGRES_PASSWORD` es fuerte (16+ caracteres aleatorios)
- [ ] Email credenciales configuradas (si usas email)

### ✅ Base de Datos
- [ ] PostgreSQL 15+ instalado en servidor
- [ ] BD `contafy_db` creada
- [ ] Usuario `contafy` con permisos correctos
- [ ] Backups automatizados configurados
- [ ] Conexión probada: `psql -U contafy -h <host>`

### ✅ Seguridad
- [ ] SSL/HTTPS certificado obtenido
- [ ] CORS configurado (si hay frontend)
- [ ] Rate limiting (opcional pero recomendado)
- [ ] Email verificable (SPF, DKIM si usas email)
- [ ] Firewall abierto SOLO para puertos 80, 443

### ✅ Docker
- [ ] `docker build` funciona sin errores
- [ ] Imagen construida: `docker images | grep contafy`
- [ ] `docker compose up` inicia sin errores
- [ ] Health check pasa: `curl http://localhost:8000/admin`

### ✅ Migraciones
- [ ] `python manage.py migrate --check` sin errores
- [ ] `python manage.py showmigrations | grep -c "\[X\]"` = 26
- [ ] No hay migraciones pendientes

### ✅ Archivos Estáticos
- [ ] `python manage.py collectstatic --noinput` funciona
- [ ] Archivos en `staticfiles/` directory
- [ ] Nginx/reverse proxy sirve desde `/app/staticfiles`

### ✅ Logging
- [ ] `LOG_LEVEL=INFO` (no DEBUG)
- [ ] Logs se guardan en archivo o central (Sentry/DataDog)
- [ ] Errores 500+ se reportan por email/Slack

---

## 🚀 Deployment en Render (Recomendado)

### Paso 1: Conectar Repositorio
1. Ir a render.com
2. "New" → "Web Service"
3. Conectar GitHub repo
4. Configurar:
   - **Name**: `contafy-prod`
   - **Environment**: `Docker`
   - **Region**: `Oregon` (o cercano a users)

### Paso 2: Variables de Entorno
En Render dashboard, configurar:
```env
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generada-aleatoriamente-50chars>
ALLOWED_HOSTS=contafy.onrender.com,tu-dominio.com
POSTGRES_DB=contafy_db
POSTGRES_USER=contafy
POSTGRES_PASSWORD=<password-fuerte-aleatorio>
POSTGRES_HOST=<db-host-render>
POSTGRES_PORT=5432
LOG_LEVEL=INFO
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=<tu-email>
EMAIL_HOST_PASSWORD=<app-password>
```

### Paso 3: Crear BD PostgreSQL en Render
1. Dashboard → "New" → "PostgreSQL"
2. Configurar:
   - **Name**: `contafy-db`
   - **PostgreSQL Version**: 15
   - **Region**: Misma que web service
3. Copiar `POSTGRES_PASSWORD` a variables de web service

### Paso 4: Deploy
1. Click "Create Web Service"
2. Render automáticamente:
   - Construye imagen Docker
   - Ejecuta migraciones
   - Collecta archivos estáticos
   - Inicia Gunicorn
3. Esperar 5-10 minutos

### Paso 5: Verificar
```bash
# Check logs en Render dashboard
# Acceder: https://contafy.onrender.com

# Verificar admin
# https://contafy.onrender.com/admin
```

---

## 🚀 Deployment Manual (AWS/DigitalOcean/VPS)

### Paso 1: Provisionar Servidor
```bash
# Ubuntu 22.04 LTS, 2GB RAM mínimo
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clonar repo
git clone <repo> /opt/contafy
cd /opt/contafy
```

### Paso 2: Configurar DNS
```bash
# Apuntar dominio A record a IP del servidor
# Esperar 5-10 minutos para propagación
```

### Paso 3: Obtener SSL Certificate
```bash
# Instalar Certbot
sudo apt update && sudo apt install -y certbot python3-certbot-nginx

# Generar certificado
sudo certbot certonly --standalone -d tu-dominio.com -d www.tu-dominio.com

# Certificado en: /etc/letsencrypt/live/tu-dominio.com/
```

### Paso 4: Configurar .env en servidor
```bash
cd /opt/contafy

# Crear .env
sudo nano .env

# Pegar (cambiar valores):
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generada>
ALLOWEDOSTS=tu-dominio.com,www.tu-dominio.com
POSTGRES_DB=contafy_prod
POSTGRES_USER=contafy
POSTGRES_PASSWORD=<aleatorio-fuerte>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
LOG_LEVEL=INFO
SECURE_SSL_REDIRECT=True

# Salvar con Ctrl+O, Enter, Ctrl+X
```

### Paso 5: Docker Compose
```bash
# Crear ubicación para datos
sudo mkdir -p /data/postgres
sudo chown -R 999:999 /data/postgres

# Editar docker-compose.yml para prod
# Cambiar volúmenes a directorios persistentes
# (opcional, por defecto usa volúmenes Docker)

# Levantar
sudo docker compose up -d

# Verificar
sudo docker compose ps
sudo docker compose logs -f web
```

### Paso 6: Nginx Reverse Proxy
```bash
# Instalar Nginx
sudo apt install -y nginx

# Crear config
sudo nano /etc/nginx/sites-available/contafy

# Contenido (reemplazar tu-dominio.com):
server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 100M;
    }

    location /static/ {
        alias /opt/contafy/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /opt/contafy/media/;
        expires 7d;
    }
}

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    return 301 https://$server_name$request_uri;
}

# Salvar y validar
sudo nginx -t

# Activar
sudo ln -sf /etc/nginx/sites-available/contafy /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

### Paso 7: Monitoreo
```bash
# Ver logs en tiempo real
sudo docker compose logs -f web

# Monitoreo básico (opcional)
sudo docker stats

# Backups automáticos
sudo crontab -e
# Agregar: 0 2 * * * docker exec contafy_db pg_dump -U contafy contafy_prod > /backups/db_$(date +\%Y\%m\%d).sql
```

---

## 🔍 Post-Deployment Verification

```bash
# Verificar conexión
curl -I https://tu-dominio.com/admin
# Esperado: HTTP/2 200

# Verificar certificado SSL
openssl s_client -connect tu-dominio.com:443 -showcerts

# Verificar BD
docker compose exec web python manage.py dbshell
# SELECT COUNT(*) FROM empresa_empresa;

# Verificar migraciones
docker compose exec web python manage.py showmigrations

# Verificar logs
docker compose logs web | tail -50

# Verificar salud
curl https://tu-dominio.com/admin
# Debe cargar sin errores
```

---

## 🆘 Troubleshooting en Producción

| Problema | Síntoma | Solución |
|----------|---------|----------|
| BD Connection Error | 500 Internal Server Error | Verificar POSTGRES_HOST, PASSWORD en .env |
| SSL Certificate Error | "Bad Certificate" | Verificar certificado con `openssl` |
| Static Files 404 | Admin sin CSS | Ejecutar `collectstatic` |
| Memory Leak | Container mata cada 1 hora | Aumentar workers o RAM |
| Email no envía | Users no reciben resets | Ver EMAIL_* variables, logs |

---

## 📊 Monitoreo Continuo

### Logs
```bash
# Real-time
docker compose logs -f web

# Últimas 100 líneas
docker compose logs --tail 100 web

# Filtrar errores
docker compose logs web | grep ERROR
```

### Métricas
```bash
# CPU/Memoria
docker stats

# Espacio disco
df -h /

# Conexiones BD
docker compose exec db psql -U contafy -c "SELECT * FROM pg_stat_activity;"
```

### Alerts (opcional)
- Sentry.io para errores Python
- DataDog para métricas
- Uptime Monitor (Pingdom, Betterstack)

---

## 🔐 Hardening Seguridad

### Settings Django
```python
# core/settings.py en producción DEBE tener:
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### BD
```sql
-- PostgreSQL en servidor
-- Cambiar password después de setup
ALTER USER contafy WITH PASSWORD '<nuevo-password-fuerte>';

-- Limitar conexiones
ALTER USER contafy CONNECTION LIMIT 50;
```

### Firewall
```bash
# Abrir SOLO puertos necesarios
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

---

## 🔄 Rollback en Caso de Emergencia

```bash
# Mantener versión anterior en git tag
git tag v1.0-prod
git push origin v1.0-prod

# Para revertir:
git checkout v1.0-prod
docker compose down
docker compose up --build

# O con Render: click "Redeploy" en versión anterior
```

---

## 📈 Performance Tuning (Opcional)

```python
# core/settings.py
CONN_MAX_AGE = 600  # Pool conexiones BD
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
    }
}

# Gunicorn workers en Dockerfile
# workers = (2 * CPU_COUNT) + 1
# Para 2 CPU: 5 workers
```

---

## ✅ Checklist Final Antes de Go-Live

- [ ] Dominio apunta a servidor
- [ ] SSL funciona (HTTPS)
- [ ] BD está accesible
- [ ] Migraciones aplicadas (26/26)
- [ ] Admin carga
- [ ] Logs sin ERRORs
- [ ] Backups automáticos funcionan
- [ ] Team fue notificado
- [ ] Runbook de emergencia escrito
- [ ] Monitoreo activo

---

**Status**: ✅ PRODUCTION-READY  
**Versión**: Django 5.2.3 + PostgreSQL 15  
**Migraciones**: NIVEL 3 Reparadas  
**Docker**: NIVEL 4 Production-Grade  
**Última actualización**: 2026-02-13
