# 🚀 GUÍA RÁPIDA - DEPLOY A RENDER

## ✅ ARCHIVOS CREADOS

Todos los archivos necesarios han sido creados:
- ✅ `empresa/views/health.py` - Health check endpoint
- ✅ `docker-entrypoint.sh` - Script de inicio automático
- ✅ `Dockerfile` - Actualizado con entrypoint
- ✅ `render.yaml` - Configuración corregida
- ✅ `core/settings.py` - Configuración para Render
- ✅ `core/urls.py` - Health check agregado
- ✅ `deploy_render.ps1` - Script de deploy

---

## 🎯 PASOS PARA DEPLOY

### PASO 1: Commit y Push (Local)

```powershell
# Ejecutar script de deploy
.\deploy_render.ps1
```

O manualmente:
```powershell
git add .
git commit -m "feat: configuración completa para Render"
git push origin main
```

---

### PASO 2: Configurar Render (Dashboard)

#### A. Crear Cuenta
1. Ve a https://render.com
2. Sign up con GitHub
3. Autoriza acceso a tu repositorio

#### B. Crear PostgreSQL Database
1. Dashboard → New → PostgreSQL
2. **Name:** `contafy-db`
3. **Database:** `contafy`
4. **User:** `contafy`
5. **Region:** Oregon (US West)
6. **Plan:** Starter ($7/mes)
7. Click "Create Database"
8. **Copiar "Internal Database URL"** (lo necesitarás)

#### C. Crear Web Service
1. Dashboard → New → Web Service
2. **Connect Repository:** Selecciona tu repo de GitHub
3. **Name:** `contafy`
4. **Region:** Oregon (US West) - misma que la BD
5. **Branch:** `main`
6. **Environment:** Docker
7. **Plan:** Starter ($7/mes)

#### D. Configurar Variables de Entorno
En la sección "Environment Variables", agregar:

```
SECRET_KEY: [Click "Generate" - se auto-genera]
DEBUG: False
DJANGO_SETTINGS_MODULE: core.settings
DATABASE_URL: [Pegar Internal Database URL de PostgreSQL]
ALLOWED_HOSTS: .onrender.com,localhost,127.0.0.1
RENDER: true
ADMIN_USERNAME: admin
ADMIN_EMAIL: admin@contafy.com
ADMIN_PASSWORD: TuPasswordSegura123!
```

#### E. Deploy
1. Click "Create Web Service"
2. Esperar 5-10 minutos
3. Ver logs en tiempo real

---

### PASO 3: Verificar Deploy

#### A. Health Check
```powershell
curl https://contafy.onrender.com/health/
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

#### B. Probar Login
1. Ir a: https://contafy.onrender.com/app-beta-2024/login/
2. Usuario: `admin`
3. Password: El que configuraste en `ADMIN_PASSWORD`

#### C. Verificar Admin
1. Ir a: https://contafy.onrender.com/admin/
2. Login con las mismas credenciales

---

## 🔍 TROUBLESHOOTING

### Error: "Application failed to respond"

**Solución:**
1. Ver logs en Render Dashboard
2. Verificar que DATABASE_URL está configurada
3. Verificar que el puerto es 8000

### Error: "DisallowedHost"

**Solución:**
```
ALLOWED_HOSTS: .onrender.com,localhost,127.0.0.1
```

### Error: "Database connection failed"

**Solución:**
1. Verificar que PostgreSQL está "Available"
2. Copiar nuevamente la "Internal Database URL"
3. Actualizar variable DATABASE_URL

### Error: "Static files not found"

**Solución:**
- El entrypoint ejecuta `collectstatic` automáticamente
- Verificar logs para ver si se ejecutó correctamente

---

## 📊 MONITOREO

### Ver Logs en Tiempo Real
1. Dashboard → Tu servicio → Logs
2. O usar Render CLI:
```powershell
npm install -g @render/cli
render login
render logs -s contafy
```

### Métricas
1. Dashboard → Tu servicio → Metrics
2. Ver CPU, memoria, requests

---

## 💰 COSTOS

- **Web Service (Starter):** $7/mes
- **PostgreSQL (Starter):** $7/mes
- **Total:** $14/mes

**Primer mes:** Gratis con créditos de prueba

---

## 🎉 PRÓXIMOS PASOS

Después del deploy exitoso:

1. **Cambiar contraseña de admin**
   - Login → Admin → Cambiar password

2. **Crear código de invitación**
   - Admin → Códigos de invitación → Agregar

3. **Registrar usuario de prueba**
   - https://contafy.onrender.com/app-beta-2024/registro/

4. **Configurar dominio personalizado** (opcional)
   - Dashboard → Settings → Custom Domain

5. **Configurar variables de producción**
   - EMAIL_HOST, EMAIL_HOST_USER, etc.

---

## 📞 SOPORTE

### Render Support
- Docs: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

### Comandos Útiles
```powershell
# Ver logs
render logs -s contafy

# Ejecutar comando
render shell -s contafy

# Reiniciar servicio
render restart -s contafy

# Ver info del servicio
render info -s contafy
```

---

## ✅ CHECKLIST FINAL

- [ ] Archivos commiteados y pusheados
- [ ] PostgreSQL creada en Render
- [ ] Web Service creado en Render
- [ ] Variables de entorno configuradas
- [ ] Deploy completado (status: Live)
- [ ] Health check responde OK
- [ ] Login funciona
- [ ] Admin accesible
- [ ] Contraseña de admin cambiada

---

**¡Listo para producción! 🎉**

**Tiempo total estimado:** 15-20 minutos
