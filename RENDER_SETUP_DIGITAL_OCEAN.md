# 🚀 Guía de Configuración de Render con PostgreSQL de DigitalOcean

## Tu información de conexión

**DATABASE_URL (completa para Render):**
```
postgresql://contafy_db_user:ycmaEMIJ9ZlAuFYQ6VVqaGqnnZdyR80D@dpg-d4aeou2li9vc73fgr0k0-a.ondigitalocean.com:25060/contafy_db?sslmode=require
```

**Desglose:**
- Usuario: `contafy_db_user`
- Contraseña: `ycmaEMIJ9ZlAuFYQ6VVqaGqnnZdyR80D`
- Host: `dpg-d4aeou2li9vc73fgr0k0-a.ondigitalocean.com`
- Puerto: `25060` (puerto estándar de DigitalOcean Managed Database)
- Base de datos: `contafy_db`
- SSL: `sslmode=require` (requerido por DigitalOcean)

---

## Pasos en Render Dashboard

### 1. Ir al servicio de Contafy
- Abre https://dashboard.render.com
- Selecciona tu servicio **contafy**

### 2. Actualizar variables de entorno
- Ve a la pestaña **Environment**
- Busca o crea la variable `DATABASE_URL`
- Reemplaza el valor con:
```
postgresql://contafy_db_user:ycmaEMIJ9ZlAuFYQ6VVqaGqnnZdyR80D@dpg-d4aeou2li9vc73fgr0k0-a.ondigitalocean.com:25060/contafy_db?sslmode=require
```
- Presiona **Save Changes**

### 3. Redeploy
- Ve a la pestaña **Deploys**
- Presiona el botón **"Deploy latest commit"** o espera a que se dispare automáticamente
- Monitorea los logs para ver si:
  - ✅ La conexión a BD es exitosa
  - ✅ Las migraciones corren correctamente
  - ✅ El servidor inicia sin errores

---

## Variables de entorno adicionales recomendadas

Si aún no las tienes en Render, añade estas:

| Variable | Valor |
|----------|-------|
| `DJANGO_SETTINGS_MODULE` | `core.settings` |
| `DEBUG` | `False` |
| `SECRET_KEY` | (generada automáticamente o pon una fuerte) |
| `ALLOWED_HOSTS` | `.onrender.com,contafy.onrender.com,localhost` |
| `CSRF_TRUSTED_ORIGINS` | `https://contafy.onrender.com` |
| `CONN_MAX_AGE` | `600` |
| `LOG_LEVEL` | `INFO` |
| `PYTHONUNBUFFERED` | `1` |

---

## Verificación local (opcional)

Si quieres probar la conexión localmente antes de Render:

```powershell
cd C:\Proyectos\contafy

# Exportar la URL como variable de entorno
$env:DATABASE_URL = "postgresql://contafy_db_user:ycmaEMIJ9ZlAuFYQ6VVqaGqnnZdyR80D@dpg-d4aeou2li9vc73fgr0k0-a.ondigitalocean.com:25060/contafy_db?sslmode=require"

# Probar que Django puede conectarse
.\.venv\Scripts\python manage.py dbshell

# O verificar con un migration check
.\.venv\Scripts\python manage.py migrate --plan
```

Si no te deja conectar localmente (firewall de DigitalOcean), no importa — Render puede conectarse sin problema.

---

## Si algo falla en Render

1. **Error: "could not translate host name"** → La URL está mal formada. Verifica que incluye `.ondigitalocean.com` y el puerto `25060`.
2. **Error: "password authentication failed"** → Usuario/contraseña incorrecta. Revisa en DigitalOcean.
3. **Error: "SSL connection refused"** → Asegúrate que `?sslmode=require` está en la URL.

---

## ¿Listo?

Una vez hayas actualizado la `DATABASE_URL` en Render, presiona **Deploy latest commit** o haz un push a master:

```powershell
cd C:\Proyectos\contafy
git add .
git commit -m "chore: update DATABASE_URL for DigitalOcean PostgreSQL"
git push origin master
```

Render debería desplegar automáticamente y conectarse a tu BD de DigitalOcean. 🎉
