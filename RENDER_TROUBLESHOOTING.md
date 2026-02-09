# Solución de Problemas - Render Deploy

## Error: "could not translate host name to address"

### Causa
El hostname de PostgreSQL no se puede resolver. Esto ocurre cuando:
1. La base de datos aún no está completamente aprovisionada
2. La variable `DATABASE_URL` tiene un hostname interno incorrecto
3. Hay un problema temporal de red/DNS en Render

### Solución

#### Opción 1: Verificar el Estado de la Base de Datos
1. Ve al Dashboard de Render: https://dashboard.render.com
2. Navega a tu base de datos `contafy-db`
3. Verifica que el estado sea **"Available"** (no "Creating" o "Suspended")
4. Si está suspendida, reactívala desde el menú

#### Opción 2: Usar la URL de Conexión Externa
1. En el Dashboard de Render, ve a tu base de datos
2. Copia la **External Connection String** (no la Internal)
3. Ve a tu servicio web `contafy`
4. En "Environment", edita la variable `DATABASE_URL`
5. Pega la External Connection String
6. Guarda y redeploy

La URL externa tiene este formato:
```
postgres://usuario:password@dpg-xxxxx-a.oregon-postgres.render.com/database
```

#### Opción 3: Recrear la Conexión en render.yaml
Si usas Blueprint (render.yaml), asegúrate de que la base de datos esté definida ANTES del servicio web:

```yaml
databases:
  - name: contafy-db
    databaseName: contafy
    user: contafy
    plan: starter
    region: oregon

services:
  - type: web
    name: contafy
    # ... resto de configuración
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: contafy-db
          property: connectionString
```

#### Opción 4: Configuración Manual de Variables
Si el problema persiste, configura manualmente:

1. **DATABASE_URL**: Copia desde el dashboard de la base de datos
2. **CONN_MAX_AGE**: `600`
3. **RENDER**: `true`
4. **ALLOWED_HOSTS**: `.onrender.com,localhost`

### Verificación Post-Deploy

Una vez que el deploy sea exitoso, verifica:

```bash
# En el Shell de Render
python manage.py check --deploy
python manage.py showmigrations
```

### Logs Útiles

Para diagnosticar, revisa los logs:
- **Build Logs**: Muestra errores durante migraciones
- **Deploy Logs**: Muestra errores al iniciar el servidor
- **Database Logs**: Muestra problemas de conexión

### Contacto con Soporte

Si el problema persiste después de 30 minutos:
1. Contacta a Render Support desde el dashboard
2. Menciona el error: "OperationalError: could not translate host name"
3. Proporciona el ID de tu base de datos y servicio web
