# Guía de Deploy en Render

## Pasos para Deploy Inicial

### 1. Crear la Base de Datos PRIMERO

**IMPORTANTE**: La base de datos debe existir antes de crear el servicio web.

1. Ve a https://dashboard.render.com
2. Click en "New +" → "PostgreSQL"
3. Configura:
   - **Name**: `contafy-db`
   - **Database**: `contafy`
   - **User**: `contafy`
   - **Region**: Oregon (o la más cercana)
   - **Plan**: Starter ($7/mes) o Free
4. Click "Create Database"
5. **ESPERA** hasta que el estado sea "Available" (puede tomar 5-10 minutos)

### 2. Verificar la Base de Datos

Una vez creada, verifica:
- Estado: **Available** ✅
- Connection String está visible
- Puedes ver tanto Internal como External URL

### 3. Crear el Servicio Web

#### Opción A: Usando Blueprint (Recomendado)

1. En el Dashboard, click "New +" → "Blueprint"
2. Conecta tu repositorio de GitHub
3. Render detectará automáticamente `render.yaml`
4. Revisa la configuración y click "Apply"
5. Render creará el servicio web y lo conectará a la base de datos existente

#### Opción B: Manual

1. Click "New +" → "Web Service"
2. Conecta tu repositorio
3. Configura:
   - **Name**: `contafy`
   - **Region**: Oregon (misma que la BD)
   - **Branch**: `main`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
   - **Plan**: Starter

4. Variables de entorno:
   ```
   SECRET_KEY=<generar-valor-aleatorio>
   DEBUG=False
   DATABASE_URL=<copiar-desde-base-de-datos>
   ALLOWED_HOSTS=.onrender.com,localhost
   RENDER=true
   ADMIN_USERNAME=admin
   ADMIN_EMAIL=admin@contafy.com
   ADMIN_PASSWORD=<tu-password-seguro>
   ```

### 4. Configurar DATABASE_URL

**Método 1: Automático (Blueprint)**
```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: contafy-db
      property: connectionString
```

**Método 2: Manual**
1. Ve a tu base de datos en el Dashboard
2. Copia la **Internal Connection String**
3. Pégala en la variable `DATABASE_URL` del servicio web

Formato esperado:
```
postgres://usuario:password@dpg-xxxxx-a/database
```

### 5. Primer Deploy

1. Render iniciará el build automáticamente
2. Monitorea los logs en tiempo real
3. El proceso incluye:
   - ✅ Instalación de dependencias
   - ✅ Migraciones de base de datos
   - ✅ Recolección de archivos estáticos
   - ✅ Creación de superusuario
   - ✅ Inicio del servidor

### 6. Verificación Post-Deploy

Una vez que el deploy sea exitoso:

1. **Health Check**: Visita `https://tu-app.onrender.com/health/`
   - Debe responder: `{"status": "ok"}`

2. **Admin Panel**: Visita `https://tu-app.onrender.com/admin/`
   - Login con las credenciales de `ADMIN_USERNAME` y `ADMIN_PASSWORD`

3. **Aplicación**: Visita `https://tu-app.onrender.com/app-beta-2024/`

## Solución de Problemas Comunes

### Error: "could not translate host name"

**Causa**: La base de datos no está completamente aprovisionada o hay un problema de DNS.

**Solución**:
1. Verifica que la base de datos esté en estado "Available"
2. Espera 5-10 minutos adicionales
3. Usa la **External Connection String** en lugar de la Internal
4. Ver `RENDER_TROUBLESHOOTING.md` para más detalles

### Error: "relation does not exist"

**Causa**: Las migraciones no se ejecutaron correctamente.

**Solución**:
```bash
# En el Shell de Render
python manage.py migrate --run-syncdb
```

### Error: "CSRF verification failed"

**Causa**: `CSRF_TRUSTED_ORIGINS` no incluye tu dominio de Render.

**Solución**: Ya está configurado en `settings.py`, pero verifica que `RENDER_EXTERNAL_URL` esté disponible.

### Servicio no inicia

**Causa**: Error en el comando de inicio o puerto incorrecto.

**Solución**: Verifica que el Start Command sea:
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
```

## Comandos Útiles

### Ejecutar en el Shell de Render

1. Ve a tu servicio web en el Dashboard
2. Click en "Shell" en el menú lateral
3. Ejecuta comandos:

```bash
# Verificar migraciones
python manage.py showmigrations

# Crear superusuario manualmente
python manage.py createsuperuser

# Verificar configuración
python manage.py check --deploy

# Verificar conexión a BD
python verify_db.py

# Ver logs en tiempo real
# (usa el Dashboard, sección "Logs")
```

## Actualizaciones y Redeploys

### Deploy Automático
- Cada push a `main` dispara un deploy automático (si `autoDeploy: true`)

### Deploy Manual
1. Ve al Dashboard
2. Click en "Manual Deploy" → "Deploy latest commit"

### Rollback
1. Ve a "Events" en el Dashboard
2. Encuentra el deploy anterior exitoso
3. Click en "Rollback to this version"

## Monitoreo

### Logs
- **Build Logs**: Errores durante la construcción
- **Deploy Logs**: Errores al iniciar el servidor
- **Application Logs**: Logs de la aplicación en ejecución

### Métricas
- CPU usage
- Memory usage
- Request count
- Response times

### Alertas
Configura alertas para:
- Deploy failures
- High error rates
- Resource limits

## Costos Estimados

### Plan Starter
- **Web Service**: $7/mes
- **PostgreSQL**: $7/mes
- **Total**: ~$14/mes

### Plan Free (Limitado)
- Web Service: Free (con limitaciones)
- PostgreSQL: Free (con limitaciones)
- Se suspende después de 90 días de inactividad

## Seguridad

### Variables de Entorno Sensibles
- Nunca commitees `.env` al repositorio
- Usa "Sync: false" para passwords en `render.yaml`
- Genera `SECRET_KEY` automáticamente

### SSL/HTTPS
- Render proporciona SSL automáticamente
- Certificados renovados automáticamente

### Backups
- PostgreSQL Starter incluye backups diarios
- Retención de 7 días
- Restauración desde el Dashboard

## Soporte

### Documentación Oficial
- https://render.com/docs
- https://render.com/docs/deploy-django

### Contacto
- Dashboard → "Help" → "Contact Support"
- Community Forum: https://community.render.com

### Archivos de Referencia
- `render.yaml` - Configuración de Blueprint
- `build.sh` - Script de construcción
- `Dockerfile` - Imagen de Docker
- `RENDER_TROUBLESHOOTING.md` - Solución de problemas detallada
