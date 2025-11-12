# 🚀 MIGRACIÓN COMPLETA A RENDER - CONTAFY ACADEMIA

**Fecha:** Enero 2025  
**Estado:** ✅ LISTO PARA DEPLOY  
**Tiempo estimado:** 15-20 minutos

---

## ✅ ARCHIVOS PREPARADOS

Todos los archivos necesarios están listos:

- ✅ `render.yaml` - Blueprint de Render (actualizado)
- ✅ `Dockerfile` - Contenedor optimizado
- ✅ `docker-entrypoint.sh` - Script de inicio automático
- ✅ `build.sh` - Script de build (alternativo)
- ✅ `empresa/views/health.py` - Health check endpoint
- ✅ `core/settings.py` - Configuración para Render
- ✅ `requirements.txt` - Dependencias completas

---

## 🎯 PASOS PARA DEPLOY

### PASO 1: Preparar Repositorio (Local)

```powershell
# 1. Verificar que todos los archivos están commiteados
git status

# 2. Si hay cambios pendientes, commitear
git add .
git commit -m "feat: migración completa a Render con Academia Duolingo"

# 3. Push a GitHub
git push origin main
```

---

### PASO 2: Crear Cuenta en Render

1. Ve a **https://render.com**
2. Click en **"Get Started"**
3. **Sign up with GitHub**
4. Autoriza acceso a tu repositorio `contafy`

---

### PASO 3: Crear Base de Datos PostgreSQL

1. En el Dashboard de Render, click **"New +"** → **"PostgreSQL"**

2. Configurar:
   - **Name:** `contafy-db`
   - **Database:** `contafy`
   - **User:** `contafy`
   - **Region:** `Oregon (US West)`
   - **PostgreSQL Version:** `16` (última estable)
   - **Plan:** `Starter` ($7/mes)

3. Click **"Create Database"**

4. Esperar 2-3 minutos hasta que el estado sea **"Available"**

5. **IMPORTANTE:** Copiar la **"Internal Database URL"**
   - Se ve así: `postgresql://contafy:xxxxx@dpg-xxxxx/contafy`
   - La necesitarás en el siguiente paso

---

### PASO 4: Crear Web Service

1. En el Dashboard, click **"New +"** → **"Web Service"**

2. **Connect Repository:**
   - Selecciona tu repositorio de GitHub: `contafy`
   - Click **"Connect"**

3. **Configuración básica:**
   - **Name:** `contafy`
   - **Region:** `Oregon (US West)` (misma que la BD)
   - **Branch:** `main`
   - **Root Directory:** (dejar vacío)
   - **Environment:** `Docker`
   - **Plan:** `Starter` ($7/mes)

4. Click **"Advanced"** para configurar variables de entorno

---

### PASO 5: Configurar Variables de Entorno

En la sección **"Environment Variables"**, agregar las siguientes:

#### Variables Obligatorias:

```
SECRET_KEY
  → Click "Generate" (Render lo genera automáticamente)

DEBUG
  → False

DJANGO_SETTINGS_MODULE
  → core.settings

DATABASE_URL
  → [Pegar la Internal Database URL que copiaste en el Paso 3]

ALLOWED_HOSTS
  → .onrender.com,localhost,127.0.0.1

RENDER
  → true
```

#### Variables de Admin (Obligatorias):

```
ADMIN_USERNAME
  → admin

ADMIN_EMAIL
  → admin@contafy.com

ADMIN_PASSWORD
  → [Tu contraseña segura - mínimo 8 caracteres]
  → Ejemplo: Contafy2025!
```

#### Variables Opcionales (Recomendadas):

```
CONN_MAX_AGE
  → 600

LOG_LEVEL
  → INFO

EMAIL_HOST
  → smtp.gmail.com

EMAIL_PORT
  → 587

EMAIL_USE_TLS
  → True

EMAIL_HOST_USER
  → [tu-email@gmail.com]

EMAIL_HOST_PASSWORD
  → [tu-app-password de Gmail]
```

---

### PASO 6: Iniciar Deploy

1. Verificar que todas las variables están configuradas

2. Click **"Create Web Service"**

3. Render comenzará el deploy automáticamente

4. **Ver logs en tiempo real:**
   - Se mostrará el progreso del build
   - Verás mensajes como:
     ```
     🔄 Esperando a PostgreSQL...
     ✅ PostgreSQL disponible
     📊 Ejecutando migraciones...
     📦 Recolectando archivos estáticos...
     👤 Verificando superusuario...
     🚀 Iniciando aplicación...
     ```

5. **Esperar 5-10 minutos** hasta que el estado sea **"Live"**

---

### PASO 7: Verificar Deploy

#### A. Health Check

Abre tu navegador o usa curl:

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

#### B. Acceder a la Aplicación

1. **URL principal:** `https://contafy.onrender.com/app-beta-2024/login/`

2. **Credenciales:**
   - Usuario: `admin`
   - Password: [La que configuraste en ADMIN_PASSWORD]

3. **Verificar que puedes:**
   - ✅ Iniciar sesión
   - ✅ Ver el dashboard
   - ✅ Acceder al admin: `https://contafy.onrender.com/admin/`

#### C. Verificar Academia Duolingo

1. Navegar a: `https://contafy.onrender.com/aprendizaje/`

2. Verificar que se carga correctamente

3. Probar crear una lección de prueba en el admin

---

## 🔧 CONFIGURACIÓN POST-DEPLOY

### 1. Cambiar Contraseña de Admin

```
1. Login como admin
2. Ir a: https://contafy.onrender.com/admin/
3. Click en tu usuario (arriba derecha)
4. "Change password"
5. Guardar nueva contraseña segura
```

### 2. Crear Código de Invitación

```
1. Admin → Códigos de invitación
2. Click "Agregar código de invitación"
3. Código: BETA2025
4. Usos máximos: 100
5. Activo: ✓
6. Guardar
```

### 3. Crear Contenido Demo de Academia

Ejecutar en Render Shell (ver sección de comandos útiles):

```bash
python manage.py shell
```

```python
from empresa.models_aprendizaje import ModuloAprendizaje, Leccion
from empresa.models import TipoEmpresa

# Crear módulo demo
tipo = TipoEmpresa.objects.first()
modulo = ModuloAprendizaje.objects.create(
    titulo="Introducción a Contabilidad",
    descripcion="Aprende los conceptos básicos",
    tipo_empresa=tipo,
    orden=1
)

# Crear lección demo
leccion = Leccion.objects.create(
    modulo=modulo,
    titulo="¿Qué es la contabilidad?",
    descripcion="Conceptos fundamentales",
    orden=1,
    puntos_xp=10,
    pasos=[
        {
            "tipo": "texto",
            "contenido": "La contabilidad es el registro sistemático de operaciones financieras"
        },
        {
            "tipo": "quiz",
            "pregunta": "¿Qué es un activo?",
            "opciones": ["Recurso económico", "Deuda", "Gasto"],
            "respuesta_correcta": 0
        }
    ]
)

print("✅ Contenido demo creado")
```

### 4. Configurar Dominio Personalizado (Opcional)

```
1. Dashboard → Tu servicio → Settings
2. Scroll a "Custom Domain"
3. Click "Add Custom Domain"
4. Ingresar: contafy.tudominio.com
5. Configurar DNS según instrucciones
6. Esperar propagación (5-30 min)
```

---

## 📊 MONITOREO Y LOGS

### Ver Logs en Tiempo Real

**Opción 1: Dashboard Web**
```
1. Dashboard → Tu servicio
2. Tab "Logs"
3. Ver logs en tiempo real
```

**Opción 2: Render CLI**
```powershell
# Instalar CLI
npm install -g @render/cli

# Login
render login

# Ver logs
render logs -s contafy

# Seguir logs en tiempo real
render logs -s contafy --tail
```

### Métricas y Performance

```
1. Dashboard → Tu servicio
2. Tab "Metrics"
3. Ver:
   - CPU Usage
   - Memory Usage
   - Request Count
   - Response Time
```

### Comandos Útiles en Render Shell

```powershell
# Abrir shell interactivo
render shell -s contafy

# Dentro del shell:
python manage.py shell              # Django shell
python manage.py dbshell            # PostgreSQL shell
python manage.py migrate            # Ejecutar migraciones
python manage.py createsuperuser    # Crear otro admin
python manage.py collectstatic      # Recolectar estáticos
```

---

## 🐛 TROUBLESHOOTING

### Error: "Application failed to respond"

**Causa:** La app no está escuchando en el puerto correcto

**Solución:**
1. Verificar logs: `render logs -s contafy`
2. Verificar que Gunicorn está corriendo en puerto 8000
3. Verificar que DATABASE_URL está configurada

### Error: "DisallowedHost at /"

**Causa:** El dominio no está en ALLOWED_HOSTS

**Solución:**
```
1. Dashboard → Environment
2. Verificar ALLOWED_HOSTS incluye: .onrender.com
3. Guardar y redeploy
```

### Error: "Database connection failed"

**Causa:** DATABASE_URL incorrecta o BD no disponible

**Solución:**
1. Verificar que PostgreSQL está "Available"
2. Copiar nuevamente la "Internal Database URL"
3. Actualizar variable DATABASE_URL
4. Manual Deploy

### Error: "Static files not found (404)"

**Causa:** collectstatic no se ejecutó

**Solución:**
1. Ver logs del build
2. Verificar que `docker-entrypoint.sh` se ejecutó
3. Manual: `render shell -s contafy` → `python manage.py collectstatic`

### Error: "502 Bad Gateway"

**Causa:** La aplicación crasheó

**Solución:**
1. Ver logs: `render logs -s contafy`
2. Buscar el error específico
3. Corregir y redeploy

### La app está lenta en el primer request

**Causa:** Render pone a dormir apps inactivas en plan Starter

**Solución:**
- Upgrade a plan Standard ($25/mes) para mantener siempre activo
- O aceptar 30-60 segundos de "cold start" después de inactividad

---

## 💰 COSTOS Y PLANES

### Plan Actual (Starter)

**Web Service:**
- Precio: $7/mes
- RAM: 512 MB
- CPU: 0.5 vCPU
- Bandwidth: 100 GB/mes
- Sleep después de 15 min inactividad

**PostgreSQL:**
- Precio: $7/mes
- Storage: 1 GB
- Backups: 7 días
- Conexiones: 97

**Total: $14/mes**

### Upgrade Recomendado (Producción)

**Web Service Standard:**
- Precio: $25/mes
- RAM: 2 GB
- CPU: 1 vCPU
- Sin sleep
- Mejor performance

**PostgreSQL Standard:**
- Precio: $20/mes
- Storage: 10 GB
- Backups: 30 días
- Conexiones: 197

**Total: $45/mes**

---

## 🔐 SEGURIDAD

### Checklist de Seguridad

- [x] DEBUG = False en producción
- [x] SECRET_KEY generada aleatoriamente
- [x] HTTPS habilitado (automático en Render)
- [x] CSRF protection activo
- [x] SQL injection protection (Django ORM)
- [x] XSS protection headers
- [ ] Cambiar contraseña de admin por defecto
- [ ] Configurar 2FA para cuenta de Render
- [ ] Configurar alertas de seguridad
- [ ] Revisar logs regularmente

### Variables Sensibles

**NUNCA commitear en Git:**
- SECRET_KEY
- DATABASE_URL
- ADMIN_PASSWORD
- EMAIL_HOST_PASSWORD
- API Keys (OpenAI, Gemini, etc.)

**Usar siempre variables de entorno en Render**

---

## 📈 PRÓXIMOS PASOS

### Inmediatos (Hoy)

1. ✅ Deploy exitoso
2. ✅ Verificar health check
3. ✅ Login como admin
4. ✅ Cambiar contraseña
5. ✅ Crear código de invitación
6. ✅ Probar Academia

### Corto Plazo (Esta Semana)

1. Crear contenido de Academia:
   - Módulos por tipo de empresa
   - Lecciones con pasos interactivos
   - Escenarios de simulación
   - Quizzes y ejercicios

2. Configurar email:
   - Gmail SMTP o SendGrid
   - Templates de notificaciones
   - Recuperación de contraseña

3. Invitar usuarios beta:
   - Compartir código de invitación
   - Recopilar feedback
   - Iterar mejoras

### Mediano Plazo (Este Mes)

1. Implementar funcionalidades de Academia:
   - Sistema de recomendaciones adaptativas
   - Gamificación completa (XP, niveles, insignias)
   - Simulaciones interactivas
   - Replay de simulaciones

2. Optimización:
   - Configurar CDN para estáticos
   - Implementar caché con Redis
   - Optimizar queries de BD

3. Monitoreo:
   - Configurar Sentry para errores
   - Implementar analytics
   - Dashboards de métricas

### Largo Plazo (Próximos Meses)

1. Escalar infraestructura:
   - Upgrade a planes Standard
   - Implementar Redis para caché
   - Configurar backups automáticos

2. Funcionalidades avanzadas:
   - Tests E2E con Playwright
   - CI/CD con GitHub Actions
   - Telemetría y KPIs
   - Localización (i18n)

3. Contenido:
   - Pipeline de importación de lecciones
   - Versionado de contenido
   - Editor visual de lecciones

---

## 📞 SOPORTE Y RECURSOS

### Documentación Oficial

- **Render Docs:** https://render.com/docs
- **Django Docs:** https://docs.djangoproject.com
- **PostgreSQL Docs:** https://www.postgresql.org/docs/

### Comunidad

- **Render Community:** https://community.render.com
- **Django Forum:** https://forum.djangoproject.com
- **Stack Overflow:** Tag `render` + `django`

### Status y Uptime

- **Render Status:** https://status.render.com
- **Incidents:** Suscribirse a notificaciones

### Comandos de Referencia Rápida

```powershell
# Ver logs
render logs -s contafy --tail

# Reiniciar servicio
render restart -s contafy

# Abrir shell
render shell -s contafy

# Ver info del servicio
render info -s contafy

# Manual deploy
render deploy -s contafy

# Ver variables de entorno
render env -s contafy
```

---

## ✅ CHECKLIST FINAL DE MIGRACIÓN

### Pre-Deploy
- [x] Archivos de configuración creados
- [x] render.yaml actualizado
- [x] Dockerfile optimizado
- [x] Health check implementado
- [x] Settings configurado para Render
- [x] Código commiteado y pusheado

### Deploy
- [ ] Cuenta de Render creada
- [ ] Repositorio conectado
- [ ] PostgreSQL creada y disponible
- [ ] Web Service creado
- [ ] Variables de entorno configuradas
- [ ] Deploy completado (status: Live)

### Verificación
- [ ] Health check responde OK
- [ ] Login funciona
- [ ] Admin accesible
- [ ] Academia carga correctamente
- [ ] Contraseña de admin cambiada
- [ ] Código de invitación creado

### Post-Deploy
- [ ] Contenido demo creado
- [ ] Email configurado (opcional)
- [ ] Dominio personalizado (opcional)
- [ ] Monitoreo configurado
- [ ] Backups verificados
- [ ] Documentación actualizada

---

## 🎉 ¡FELICIDADES!

Tu aplicación CONTAFY con Academia Duolingo está ahora en producción en Render.

**URL de tu app:** https://contafy.onrender.com

**Próximo paso:** Crear contenido educativo y empezar a invitar usuarios beta.

---

**Tiempo total de migración:** 15-20 minutos  
**Última actualización:** Enero 2025  
**Preparado por:** Amazon Q Developer
