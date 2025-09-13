# 🚀 APLICAR RESTAURACIÓN COMPLETA

## Comandos para Ejecutar en Orden

### 1. Subir Cambios
```bash
git add .
git commit -m "restore: RecommendationService and add migration for UX fields"
git push heroku main
```

### 2. Aplicar Migraciones
```bash
# Aplicar nueva migración con campos UX
heroku run python manage.py migrate

# Verificar que se aplicó correctamente
heroku run python manage.py showmigrations empresa
```

### 3. Cargar Contenido Demo
```bash
# Cargar módulos, lecciones y escenarios
heroku run python manage.py crear_contenido_demo

# Verificar en admin que se creó contenido
heroku run python manage.py shell -c "from empresa.models_aprendizaje import ModuloAprendizaje; print(f'Módulos: {ModuloAprendizaje.objects.count()}')"
```

### 4. Verificar Funcionamiento
```bash
# Ver logs en tiempo real
heroku logs --tail

# Verificar que no hay errores 500
curl -I https://contafy-pruebas-30fdb804cc25.herokuapp.com/app-beta-2024/aprendizaje/
```

## Funcionalidades Restauradas

### ✅ Backend
- RecommendationService funcionando
- Campos slug en ModuloAprendizaje y Leccion
- Modelo AsientoAudit para sandbox
- Índices de performance
- Timestamps automáticos

### ✅ Frontend
- Dashboard con recomendaciones personalizadas
- Módulos con barras de progreso
- Navegación mejorada
- Estadísticas visuales

### ✅ APIs REST
- `/api/academia/modulos/`
- `/api/academia/lecciones/`
- `/api/academia/simulacion/start/`
- `/api/academia/recomendaciones/`

## Validación Post-Aplicación

### 1. Dashboard Principal
- ✅ `/aprendizaje/` carga sin errores
- ✅ Muestra módulos con progreso
- ✅ Recomendaciones aparecen
- ✅ Estadísticas de usuario visibles

### 2. Navegación
- ✅ Click en módulos funciona
- ✅ Lecciones se abren correctamente
- ✅ Simulaciones se pueden iniciar

### 3. Admin
- ✅ Modelos de aprendizaje editables
- ✅ Contenido demo visible
- ✅ AsientoAudit aparece en admin

## Si Hay Problemas

### Error en Migración
```bash
# Ver detalles del error
heroku run python manage.py migrate --verbosity=2

# Rollback si es necesario
heroku run python manage.py migrate empresa 0019
```

### Error 500 Persiste
```bash
# Ver logs detallados
heroku logs --tail

# Verificar imports
heroku run python manage.py shell -c "from empresa.services.recommendation_service import RecommendationService; print('OK')"
```

### Contenido No Aparece
```bash
# Verificar que se creó
heroku run python manage.py shell -c "from empresa.models_aprendizaje import *; print(f'Módulos: {ModuloAprendizaje.objects.count()}, Lecciones: {Leccion.objects.count()}')"

# Re-ejecutar comando demo
heroku run python manage.py crear_contenido_demo
```

**EJECUTAR COMANDOS EN ORDEN Y VERIFICAR CADA PASO**