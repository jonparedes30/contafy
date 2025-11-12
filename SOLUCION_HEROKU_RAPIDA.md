# ⚡ SOLUCIÓN RÁPIDA - HEROKU NO ABRE
## Pasos Inmediatos para Resolver el Problema

---

## 🔴 PROBLEMA
El sistema CONTAFY no abre en Heroku

---

## ✅ SOLUCIÓN EN 3 PASOS

### PASO 1: Ver los Logs (OBLIGATORIO)

```powershell
# Ejecutar en PowerShell
heroku logs -n 200 --app contafy-pruebas
```

**Busca uno de estos errores:**
- `ValueError: SECRET_KEY debe ser configurada`
- `relation "empresa_usuario" does not exist`
- `DisallowedHost`
- `Error R10 (Boot timeout)`
- `bash: gunicorn: command not found`

---

### PASO 2: Aplicar Solución Según el Error

#### ❌ Error: "SECRET_KEY debe ser configurada"

```powershell
# Generar y configurar SECRET_KEY
$SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(50))"
heroku config:set SECRET_KEY="$SECRET_KEY" --app contafy-pruebas
heroku restart --app contafy-pruebas
```

#### ❌ Error: "relation does not exist" (Base de datos)

```powershell
# Ejecutar migraciones
heroku run python manage.py migrate --app contafy-pruebas
heroku restart --app contafy-pruebas
```

#### ❌ Error: "DisallowedHost"

```powershell
# Configurar ALLOWED_HOSTS
heroku config:set ALLOWED_HOSTS="contafy-pruebas-30fdb804cc25.herokuapp.com,.herokuapp.com" --app contafy-pruebas
heroku restart --app contafy-pruebas
```

#### ❌ Error: "gunicorn: command not found"

```powershell
# Verificar que gunicorn está en requirements.txt
cat requirements.txt | Select-String gunicorn

# Si no está, agregarlo
Add-Content requirements.txt "gunicorn==21.2.0"
git add requirements.txt
git commit -m "add gunicorn"
git push heroku main
```

---

### PASO 3: Configuración Completa (Si nada funciona)

```powershell
# Ejecutar script automático
.\setup_heroku.ps1
```

O manualmente:

```powershell
# 1. SECRET_KEY
$SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(50))"
heroku config:set SECRET_KEY="$SECRET_KEY" --app contafy-pruebas

# 2. DEBUG
heroku config:set DEBUG=False --app contafy-pruebas

# 3. ALLOWED_HOSTS
heroku config:set ALLOWED_HOSTS="contafy-pruebas-30fdb804cc25.herokuapp.com,.herokuapp.com" --app contafy-pruebas

# 4. Migraciones
heroku run python manage.py migrate --app contafy-pruebas

# 5. Estáticos
heroku run python manage.py collectstatic --noinput --app contafy-pruebas

# 6. Reiniciar
heroku restart --app contafy-pruebas

# 7. Abrir
heroku open --app contafy-pruebas
```

---

## 🔍 VERIFICACIÓN

### 1. Ver Estado
```powershell
heroku ps --app contafy-pruebas
```

**Debe mostrar:**
```
=== web (Free): gunicorn core.wsgi --log-file -
web.1: up 2025/01/12 10:00:00 (~ 1m ago)
```

### 2. Ver Variables
```powershell
heroku config --app contafy-pruebas
```

**Debe incluir:**
- `SECRET_KEY`
- `DATABASE_URL`
- `DEBUG=False`
- `ALLOWED_HOSTS`

### 3. Probar en Navegador
```powershell
heroku open --app contafy-pruebas
```

---

## 📋 CHECKLIST RÁPIDO

- [ ] Logs revisados
- [ ] SECRET_KEY configurada
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS configurado
- [ ] Postgres provisionado
- [ ] Migraciones aplicadas
- [ ] Estáticos recolectados
- [ ] Aplicación reiniciada
- [ ] Dyno web corriendo
- [ ] Aplicación abre en navegador

---

## 🆘 SI NADA FUNCIONA

### Opción 1: Rollback
```powershell
# Ver versiones
heroku releases --app contafy-pruebas

# Volver a versión anterior que funcionaba
heroku rollback v123 --app contafy-pruebas
```

### Opción 2: Recrear App
```powershell
# Crear nueva app
heroku create contafy-nuevo

# Agregar Postgres
heroku addons:create heroku-postgresql:mini --app contafy-nuevo

# Configurar variables
.\setup_heroku.ps1  # Editar con nuevo nombre

# Deploy
git push heroku main
```

### Opción 3: Soporte
```powershell
# Ver documentación completa
cat DIAGNOSTICO_HEROKU.md

# Contactar soporte con logs
heroku logs -n 500 --app contafy-pruebas > heroku-error.log
```

---

## 💡 TIPS

1. **Siempre revisa los logs primero**
   ```powershell
   heroku logs --tail --app contafy-pruebas
   ```

2. **Verifica que el dyno esté corriendo**
   ```powershell
   heroku ps --app contafy-pruebas
   ```

3. **Reinicia después de cada cambio**
   ```powershell
   heroku restart --app contafy-pruebas
   ```

4. **Usa el script automático**
   ```powershell
   .\setup_heroku.ps1
   ```

---

## 📞 COMANDOS ÚTILES

```powershell
# Ver logs en tiempo real
heroku logs --tail --app contafy-pruebas

# Ejecutar comando en Heroku
heroku run python manage.py shell --app contafy-pruebas

# Ver info de Postgres
heroku pg:info --app contafy-pruebas

# Conectar a Postgres
heroku pg:psql --app contafy-pruebas

# Ver métricas
heroku metrics --app contafy-pruebas

# Reiniciar
heroku restart --app contafy-pruebas

# Abrir
heroku open --app contafy-pruebas
```

---

**Última actualización:** 2025
**Tiempo estimado de solución:** 5-10 minutos
