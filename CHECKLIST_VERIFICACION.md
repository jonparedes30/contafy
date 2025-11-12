# ✅ CHECKLIST DE VERIFICACIÓN - CONTAFY
## Lista de Verificación Post-Correcciones

**Fecha:** 2025
**Versión:** 1.0

---

## VERIFICACIÓN INMEDIATA (Antes de Commit)

### 1. Sintaxis y Imports
- [ ] Ejecutar `python manage.py check`
- [ ] Verificar que no hay errores de sintaxis
- [ ] Confirmar que todos los imports existen
- [ ] Verificar que no hay imports circulares

```bash
python manage.py check
```

**Resultado esperado:** `System check identified no issues (0 silenced).`

---

### 2. Migraciones
- [ ] Verificar que no hay migraciones pendientes
- [ ] Confirmar que la BD está actualizada

```bash
python manage.py showmigrations
python manage.py migrate --check
```

**Resultado esperado:** Todas las migraciones aplicadas

---

### 3. Tests Unitarios
- [ ] Ejecutar suite completa de tests
- [ ] Verificar que todos los tests pasan
- [ ] Revisar warnings si los hay

```bash
python manage.py test empresa.tests
```

**Resultado esperado:** `OK` en todos los tests

---

## VERIFICACIÓN EN DESARROLLO

### 4. URLs y Routing
- [ ] Verificar que todas las URLs se cargan correctamente
- [ ] Confirmar que no hay URLs duplicadas
- [ ] Verificar que endpoints de debug están protegidos

```bash
python manage.py show_urls | grep -E "(test|debug)"
```

**Resultado esperado:** No debe mostrar URLs de test/debug si DEBUG=False

---

### 5. Servidor de Desarrollo
- [ ] Iniciar servidor sin errores
- [ ] Verificar que no hay warnings críticos
- [ ] Confirmar que el servidor responde

```bash
python manage.py runserver
```

**Verificar en navegador:**
- [ ] http://localhost:8000/app-beta-2024/ (debe redirigir a login)
- [ ] http://localhost:8000/app-beta-2024/login/ (debe cargar)

---

### 6. Autenticación y Permisos
- [ ] Login funciona correctamente
- [ ] Logout funciona correctamente
- [ ] Registro con código de invitación funciona
- [ ] Permisos de empleados se respetan

**Pasos:**
1. Crear usuario de prueba
2. Login
3. Verificar acceso a menús según permisos
4. Logout

---

### 7. Menú y Navegación
- [ ] Menú se carga correctamente
- [ ] No hay enlaces rotos
- [ ] Menú de manufactura muestra mensaje informativo
- [ ] Todos los enlaces funcionan

**Verificar para cada tipo de empresa:**
- [ ] Comercial
- [ ] Servicios
- [ ] Manufactura

---

### 8. APIs de Academia
- [ ] GET /api/academia/modulos/ funciona
- [ ] Paginación funciona correctamente
- [ ] GET /api/academia/lecciones/ funciona
- [ ] GET /api/academia/escenarios/ funciona

```bash
# Con autenticación
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/academia/modulos/
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/academia/modulos/?page=2
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/academia/modulos/?page_size=5
```

**Verificar respuesta:**
```json
{
  "count": 20,
  "next": "http://localhost:8000/api/academia/modulos/?page=2",
  "previous": null,
  "results": [...]
}
```

---

### 9. Simulaciones
- [ ] Crear simulación funciona
- [ ] Completar simulación funciona
- [ ] Intentar completar dos veces retorna error 400
- [ ] XP se otorga correctamente

**Pasos:**
1. Iniciar simulación
2. Completar simulación
3. Intentar completar de nuevo
4. Verificar error: "Esta simulación ya fue completada"

---

### 10. CSRF Protection
- [ ] Formularios incluyen {% csrf_token %}
- [ ] AJAX requests incluyen CSRF token
- [ ] POST sin token CSRF falla con 403

**Verificar en:**
- [ ] Editar empresa
- [ ] Editar usuario
- [ ] Eliminar empleado
- [ ] Gestión de poderes

---

### 11. Endpoints de Debug (Solo en DEBUG=True)
- [ ] Con DEBUG=True, endpoints accesibles
- [ ] Con DEBUG=False, endpoints retornan 404

```bash
# Con DEBUG=True
curl -I http://localhost:8000/app-beta-2024/test/filtros/
# Debe retornar 200

# Con DEBUG=False
curl -I http://localhost:8000/app-beta-2024/test/filtros/
# Debe retornar 404
```

---

### 12. Funcionalidad Core
- [ ] Crear venta funciona
- [ ] Editar venta funciona
- [ ] Eliminar venta funciona (sin URL duplicada)
- [ ] Crear gasto funciona
- [ ] Crear compra funciona
- [ ] Reportes se generan correctamente

---

## VERIFICACIÓN EN STAGING

### 13. Deploy a Staging
- [ ] Código pusheado a repositorio
- [ ] CI/CD ejecutado exitosamente
- [ ] Aplicación desplegada en staging
- [ ] Migraciones aplicadas

```bash
git add .
git commit -m "fix: aplicar correcciones críticas de seguridad y performance"
git push origin main
```

---

### 14. Smoke Tests en Staging
- [ ] Aplicación carga correctamente
- [ ] Login funciona
- [ ] Menú se muestra correctamente
- [ ] APIs responden
- [ ] No hay errores 500 en logs

---

### 15. Seguridad en Staging
- [ ] Endpoints de debug NO accesibles
- [ ] CSRF protection activa
- [ ] HTTPS funcionando
- [ ] Headers de seguridad configurados

```bash
# Verificar endpoints de debug
curl -I https://staging.contafy.com/app-beta-2024/debug/datos/
# Debe retornar 404

# Verificar CSRF
curl -X POST https://staging.contafy.com/app-beta-2024/editar/ \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Test"}'
# Debe retornar 403 Forbidden
```

---

### 16. Performance en Staging
- [ ] Tiempos de respuesta aceptables
- [ ] Paginación funciona correctamente
- [ ] No hay queries N+1
- [ ] Memoria estable

**Herramientas:**
- Django Debug Toolbar
- New Relic / Sentry
- Logs de aplicación

---

### 17. Testing de Usuario en Staging
- [ ] Flujo completo de venta
- [ ] Flujo completo de compra
- [ ] Flujo completo de gasto
- [ ] Generación de reportes
- [ ] Academia y simulaciones
- [ ] Exportaciones (Excel, PDF)

---

### 18. Compatibilidad de Navegadores
- [ ] Chrome (última versión)
- [ ] Firefox (última versión)
- [ ] Safari (última versión)
- [ ] Edge (última versión)
- [ ] Móvil (iOS Safari)
- [ ] Móvil (Android Chrome)

---

### 19. Responsive Design
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Móvil (375x667)
- [ ] Móvil (414x896)

---

### 20. Logs y Monitoreo
- [ ] No hay errores en logs
- [ ] Warnings revisados
- [ ] Métricas de performance normales
- [ ] Alertas configuradas

---

## VERIFICACIÓN PRE-PRODUCCIÓN

### 21. Backup
- [ ] Backup de base de datos creado
- [ ] Backup de archivos estáticos creado
- [ ] Backup de configuración creado
- [ ] Plan de rollback documentado

---

### 22. Documentación
- [ ] CHANGELOG actualizado
- [ ] Documentación de APIs actualizada
- [ ] README actualizado si es necesario
- [ ] Equipo notificado de cambios

---

### 23. Comunicación
- [ ] Stakeholders notificados
- [ ] Equipo de soporte informado
- [ ] Usuarios clave notificados (si aplica)
- [ ] Ventana de mantenimiento comunicada (si aplica)

---

### 24. Rollback Plan
- [ ] Procedimiento de rollback documentado
- [ ] Comandos de rollback probados
- [ ] Responsables de rollback identificados
- [ ] Tiempo estimado de rollback conocido

---

## VERIFICACIÓN POST-PRODUCCIÓN

### 25. Deploy a Producción
- [ ] Código desplegado exitosamente
- [ ] Migraciones aplicadas
- [ ] Servicios reiniciados
- [ ] Health check pasando

---

### 26. Smoke Tests en Producción
- [ ] Aplicación carga correctamente
- [ ] Login funciona
- [ ] APIs responden
- [ ] No hay errores 500
- [ ] Logs limpios

---

### 27. Monitoreo Activo (Primeras 24h)
- [ ] Tasa de errores normal
- [ ] Tiempos de respuesta normales
- [ ] Uso de CPU/memoria normal
- [ ] No hay alertas críticas

---

### 28. Feedback de Usuarios
- [ ] No hay reportes de errores críticos
- [ ] Funcionalidad core operativa
- [ ] Performance aceptable
- [ ] UX sin problemas mayores

---

## MÉTRICAS DE ÉXITO

### Seguridad
- [ ] 0 endpoints de debug expuestos en producción
- [ ] 0 errores CSRF reportados
- [ ] 0 vulnerabilidades críticas

### Performance
- [ ] Tiempo de respuesta APIs < 500ms (p95)
- [ ] Paginación reduce carga en 50%+
- [ ] 0 timeouts reportados

### Estabilidad
- [ ] Uptime > 99.9%
- [ ] 0 errores 500 relacionados con cambios
- [ ] 0 rollbacks necesarios

### UX
- [ ] 0 reportes de enlaces rotos
- [ ] Feedback positivo de usuarios de manufactura
- [ ] 0 confusión sobre URLs

---

## PROBLEMAS CONOCIDOS Y WORKAROUNDS

### Problema 1: CSRF en AJAX
**Síntoma:** Error 403 en peticiones AJAX POST
**Workaround:** Agregar token CSRF en headers
```javascript
headers: {
    'X-CSRFToken': getCookie('csrftoken')
}
```

### Problema 2: Paginación en Cliente Antiguo
**Síntoma:** Cliente espera array, recibe objeto paginado
**Workaround:** Cliente debe acceder a `response.results`

---

## CONTACTOS DE EMERGENCIA

**Desarrollador Principal:** [Nombre]
**DevOps:** [Nombre]
**DBA:** [Nombre]
**Soporte:** [Email/Teléfono]

---

## NOTAS ADICIONALES

### Cambios que Requieren Atención del Frontend
1. **CSRF Tokens:** Asegurar que todos los POST incluyan token
2. **Paginación:** Actualizar clientes de API para manejar respuesta paginada
3. **URL Eliminada:** Cambiar `api_eliminar_venta` a `eliminar_venta`

### Cambios que Requieren Atención del Backend
1. **Imports:** Verificar que todos los imports directos funcionan
2. **Settings:** Confirmar que DEBUG=False en producción
3. **Logs:** Monitorear logs para errores relacionados con cambios

---

## FIRMA DE APROBACIÓN

- [ ] **Desarrollador:** _________________ Fecha: _______
- [ ] **QA:** _________________ Fecha: _______
- [ ] **DevOps:** _________________ Fecha: _______
- [ ] **Product Owner:** _________________ Fecha: _______

---

**Última actualización:** 2025
**Próxima revisión:** Post-deploy a producción
**Estado:** ⏳ Pendiente de verificación
