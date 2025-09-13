# 🚨 EMERGENCY FIX - Academia Error 500

## Cambios Aplicados

### ✅ Fixes Críticos
1. **Comentado import RecomendacionService** - Puede no existir en producción
2. **Deshabilitadas recomendaciones** - Fallback a lista vacía
3. **Try-catch en GamificacionService** - Fallback a perfil básico
4. **Protegido acceso a usuario.empresa** - Previene AttributeError

### 🔧 Subir Fix Inmediatamente

```bash
git add .
git commit -m "emergency fix: disable problematic services causing 500 error"
git push heroku main
```

### 📋 Verificaciones Post-Deploy

1. **Verificar carga**: `/aprendizaje/` debe cargar sin error 500
2. **Funcionalidad básica**: Dashboard debe mostrar módulos
3. **Navegación**: Enlaces deben funcionar

### 🎯 Estado Esperado

- ✅ Dashboard carga sin errores
- ✅ Módulos se muestran (si existen)
- ✅ Navegación básica funciona
- ⚠️ Recomendaciones temporalmente deshabilitadas
- ⚠️ Estadísticas pueden ser básicas

### 🔄 Restauración Completa

Una vez confirmado que funciona:

```bash
# 1. Aplicar migraciones
heroku run python manage.py migrate

# 2. Cargar contenido demo
heroku run python manage.py crear_contenido_demo

# 3. Verificar modelos en admin
heroku run python manage.py shell
```

### 🚨 Si Persiste Error 500

Revisar logs de Heroku:
```bash
heroku logs --tail
```

Posibles causas restantes:
- Migraciones pendientes críticas
- Imports de modelos que no existen
- Template que referencia campos inexistentes

**PRIORIDAD MÁXIMA: Restaurar servicio básico funcionando**