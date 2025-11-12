# ✅ RENDER - LISTO PARA DEPLOY

## Archivos Preparados
- ✅ render.yaml
- ✅ Dockerfile  
- ✅ docker-entrypoint.sh
- ✅ build.sh
- ✅ empresa/views/health.py
- ✅ core/settings.py (con config Render)

## Deploy Rápido

### 1. Push código
```powershell
git add .
git commit -m "feat: migración Render"
git push origin main
```

### 2. En Render Dashboard

**PostgreSQL:**
- New → PostgreSQL
- Name: `contafy-db`
- Plan: Starter ($7/mes)
- Copiar Internal Database URL

**Web Service:**
- New → Web Service
- Connect repo: contafy
- Environment: Docker
- Plan: Starter ($7/mes)

**Variables de entorno:**
```
SECRET_KEY: [Generate]
DEBUG: False
DJANGO_SETTINGS_MODULE: core.settings
DATABASE_URL: [Pegar URL de PostgreSQL]
ALLOWED_HOSTS: .onrender.com,localhost,127.0.0.1
RENDER: true
ADMIN_USERNAME: admin
ADMIN_EMAIL: admin@contafy.com
ADMIN_PASSWORD: [Tu password]
```

### 3. Verificar
- Health: https://contafy.onrender.com/health/
- Login: https://contafy.onrender.com/app-beta-2024/login/
- Academia: https://contafy.onrender.com/aprendizaje/

## Costo Total
$14/mes (Web $7 + DB $7)

## Docs Completas
Ver: MIGRACION_RENDER_COMPLETA.md
