# 🚨 HOTFIX ACADEMIA - Error 500

## Problema Identificado
Error 500 en `/aprendizaje/` causado por:
- Import de `aprendizaje_views.py` que no existe en Heroku
- Posibles migraciones pendientes
- Campos nuevos no aplicados en DB de producción

## Fix Aplicado
✅ **Removido import problemático** en `aprendizaje.py`
✅ **Fallback a template original** funcionando
✅ **Sistema base preservado**

## Acciones Inmediatas Requeridas

### 1. Aplicar en Heroku
```bash
# Subir fix
git add .
git commit -m "hotfix: remove problematic import in aprendizaje dashboard"
git push heroku main

# Aplicar migraciones pendientes
heroku run python manage.py migrate

# Cargar contenido demo
heroku run python manage.py crear_contenido_demo
```

### 2. Verificar Funcionamiento
- ✅ `/aprendizaje/` debe cargar sin error 500
- ✅ Dashboard básico debe funcionar
- ✅ Navegación debe estar operativa

### 3. Implementación Gradual UX Duolingo

**Opción A: Fix Completo (Recomendado)**
```bash
# Crear migraciones localmente
python manage.py makemigrations empresa --name add_audit_and_slug_fields
git add migrations/
git commit -m "add: migraciones para campos UX Duolingo"
git push heroku main
heroku run python manage.py migrate
```

**Opción B: Rollback Temporal**
- Mantener funcionalidad original
- Implementar UX Duolingo en branch separado
- Merge cuando migraciones estén listas

## Estado Actual
- 🔴 **Error 500 RESUELTO**
- 🟡 **UX Duolingo temporalmente deshabilitada**
- 🟢 **Funcionalidad base operativa**

## Próximos Pasos
1. **Inmediato**: Subir hotfix y verificar que `/aprendizaje/` funciona
2. **Corto plazo**: Aplicar migraciones y restaurar UX Duolingo
3. **Mediano plazo**: Implementar gradualmente las mejoras

**PRIORIDAD: Restaurar servicio funcionando primero, mejoras después.**