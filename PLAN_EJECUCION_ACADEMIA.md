# Plan de Ejecución - Academia CONTAFY
## Transformación a experiencia tipo Duolingo

### Resumen Ejecutivo
**Objetivo**: Convertir la Academia CONTAFY en una plataforma de aprendizaje gamificada tipo Duolingo
**Duración total**: 15-20 días hábiles (3-4 sprints)
**Equipo requerido**: 1-2 desarrolladores, 1 QA, 1 editor de contenido

---

## FASE 0 — Preparación y Setup (0.5 días)
**Prioridad**: CRÍTICA
**Responsable**: Dev Lead

### Objetivos
- Rama de trabajo segura
- Entorno reproducible
- Tests básicos funcionando

### Tareas Concretas
1. **Setup inicial** (30 min)
   ```powershell
   git checkout -b feature/academy-launch
   git push -u origin feature/academy-launch
   ```

2. **Validación entorno** (1 hora)
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   $env:DJANGO_SETTINGS_MODULE='core.test_settings'
   python manage.py test empresa.tests -q
   Remove-Item Env:\DJANGO_SETTINGS_MODULE
   ```

3. **Limpieza proyecto** (30 min)
   - Verificar .gitignore actualizado
   - Documentar dependencias faltantes

### Criterios de Aceptación
- ✅ Branch `feature/academy-launch` creado
- ✅ Tests unitarios básicos pasan (>95%)
- ✅ Entorno local reproducible documentado

---

## FASE 1 — Admin y Gestión de Contenido (3-4 días)
**Prioridad**: CRÍTICA
**Responsable**: Backend Dev + Editor

### Objetivos
- Editores pueden crear/modificar contenido sin código
- Contenido demo disponible para testing
- Validaciones robustas

### Tareas Concretas

#### Día 1-2: Modelos y Admin
1. **Revisar/completar modelos** (4 horas)
   - Archivo: `empresa/models_aprendizaje.py`
   - Campos faltantes: `tiempo_estimado`, `dificultad`, `visible`, `orden`
   - Validaciones JSON en `clean()`

2. **Admin interface** (4 horas)
   - Archivo: `empresa/admin.py`
   - ModelAdmin con inlines para pasos
   - Filtros por tipo_empresa, dificultad
   - Preview de contenido JSON

#### Día 3: Contenido Demo
3. **Comando de contenido demo** (6 horas)
   - Archivo: `empresa/management/commands/crear_contenido_demo.py`
   - 3 módulos × 5 lecciones × 3 escenarios mínimo
   - Datos realistas para pymes ecuatorianas

#### Día 4: Testing y Refinamiento
4. **Tests y validaciones** (2 horas)
   - Tests para validaciones de modelos
   - Tests para comando demo

### Entregables
- Admin funcional con CRUD completo
- Comando `python manage.py crear_contenido_demo` funcional
- 15+ lecciones demo cargadas

### Criterios de Aceptación
- ✅ Editor puede crear módulo completo en <10 min
- ✅ Validaciones JSON funcionan (rechaza malformed)
- ✅ Comando demo carga sin errores
- ✅ Admin muestra preview de pasos

---

## FASE 2 — Sandbox Seguro y Contabilidad (2-3 días)
**Prioridad**: CRÍTICA
**Responsable**: Backend Dev

### Objetivos
- Simulaciones no persisten datos reales
- Sin efectos externos (emails, APIs)
- Contabilidad balanceada (DEBE = HABER)

### Tareas Concretas

#### Día 1: Sandbox Service
1. **Consolidar SimulacionService** (4 horas)
   - Archivo: `empresa/services/simulacion_service.py`
   - Usar `transaction.savepoint()` para rollback
   - Flag `es_sandbox` en todas las operaciones

2. **Bloquear side-effects** (2 horas)
   - Patch `send_mail`, `requests`, `boto3` en sandbox
   - Deshabilitar `.delay()` de Celery

#### Día 2: Contabilidad Robusta
3. **Forzar Decimal y balance** (4 horas)
   - Archivo: `empresa/services/contabilidad_service.py`
   - Todos los cálculos en `Decimal`
   - Validación DEBE = HABER en cada asiento

4. **Tests de integridad** (2 horas)
   - Tests para cada tipo de simulación
   - Verificar balance contable

### Entregables
- SimulacionService consolidado
- Tests sandbox completos
- Contabilidad balanceada garantizada

### Criterios de Aceptación
- ✅ Simulación sandbox no crea asientos reales
- ✅ No se envían emails durante sandbox
- ✅ Balance contable siempre cuadra
- ✅ Tests de concurrencia pasan

---

## FASE 3 — APIs REST y Progreso (1-2 días)
**Prioridad**: ALTA
**Responsable**: Backend Dev

### Objetivos
- APIs REST para frontend
- Progreso por tipo_empresa
- Sistema de recomendaciones básico

### Tareas Concretas

#### Día 1: APIs Core
1. **Endpoints simulación** (4 horas)
   - `POST /api/simulacion/start/`
   - `GET /api/simulacion/<id>/`
   - `POST /api/simulacion/<id>/guardar/`
   - `POST /api/simulacion/<id>/finalizar/`

2. **Endpoints progreso** (2 horas)
   - `GET /api/progreso/rutas/`
   - `POST /api/progreso/marcar-paso/`

#### Día 2: Recomendaciones
3. **RecommendationService** (4 horas)
   - Archivo: `empresa/services/recommendation_service.py`
   - Lógica simple: nivel + tipo_empresa + rendimiento
   - Endpoint `GET /api/recomendaciones/`

### Entregables
- 7 endpoints REST documentados
- RecommendationService funcional
- Tests de API completos

### Criterios de Aceptación
- ✅ APIs devuelven JSON válido
- ✅ Filtrado por tipo_empresa funciona
- ✅ Progreso se guarda correctamente
- ✅ Recomendaciones son relevantes

---

## FASE 4 — Frontend UX Duolingo (4-6 días)
**Prioridad**: ALTA
**Responsable**: Frontend Dev + UX

### Objetivos
- UI por pasos clara y atractiva
- Modal interactivo para simulaciones
- Feedback inmediato y gamificación
- Responsive y accesible

### Tareas Concretas

#### Día 1-2: Estructura Base
1. **Refactor JS y CSS** (6 horas)
   - Mover a `static/empresa/js/aprendizaje.js`
   - CSS modular en `static/empresa/css/aprendizaje.css`
   - Eliminar JS inline

2. **Componentes reutilizables** (4 horas)
   - Modal simulación configurable
   - Toast system con Bootstrap
   - Progress bars animadas

#### Día 3-4: Interactividad
3. **Modal simulación avanzado** (8 horas)
   - Inputs dinámicos según escenario
   - Validación client-side
   - Autosave cada 30 segundos
   - Preview de resultados

4. **Sistema de pasos** (4 horas)
   - Navegación paso a paso
   - Animaciones de transición
   - Marcadores visuales de progreso

#### Día 5-6: Gamificación y Polish
5. **XP y feedback** (6 horas)
   - Toast animado de XP ganado
   - Actualización header en tiempo real
   - Celebraciones micro (confetti, sonidos)

6. **Responsive y a11y** (4 horas)
   - Mobile-first design
   - ARIA labels
   - Keyboard navigation

### Entregables
- UI completamente refactorizada
- Modal simulación interactivo
- Sistema de gamificación visual
- Tests de accesibilidad

### Criterios de Aceptación
- ✅ Usuario completa lección en <5 min
- ✅ Modal simulación es intuitivo
- ✅ XP se actualiza inmediatamente
- ✅ Funciona en mobile y desktop
- ✅ Pasa tests de accesibilidad básicos

---

## FASE 5 — Replay y Analítica (2-3 días)
**Prioridad**: MEDIA
**Responsable**: Backend Dev

### Objetivos
- Eventos de simulación guardados
- Capacidad de replay para debugging
- Métricas básicas para mejora

### Tareas Concretas

#### Día 1: Modelo de Eventos
1. **SimulacionEvento model** (3 horas)
   - FK a SimulacionUsuario
   - Campos: timestamp, tipo, payload JSON
   - Índices para queries rápidas

2. **Endpoints eventos** (3 horas)
   - `POST /api/eventos/` para enviar desde frontend
   - Batch processing para performance

#### Día 2: Admin y Replay
3. **Admin interface** (4 horas)
   - Lista de simulaciones con eventos
   - Botón "Replay" que muestra timeline
   - Export CSV para análisis

4. **Replay viewer** (2 horas)
   - Template simple que reproduce eventos
   - Timeline visual básica

#### Día 3: Métricas
5. **Dashboard básico** (4 horas)
   - Tiempo promedio por simulación
   - Tasa de completación por tipo
   - Puntos de abandono comunes

### Entregables
- Sistema de eventos completo
- Admin con replay funcional
- Dashboard de métricas básicas

### Criterios de Aceptación
- ✅ Eventos se guardan sin impacto en performance
- ✅ Admin puede reproducir sesión completa
- ✅ Métricas muestran insights útiles
- ✅ Export CSV funciona

---

## FASE 6 — Tests E2E y CI con Postgres (3-4 días)
**Prioridad**: ALTA
**Responsable**: QA + DevOps

### Objetivos
- Tests end-to-end del flujo completo
- CI con Postgres para validar concurrencia
- Cobertura de casos edge

### Tareas Concretas

#### Día 1-2: Setup E2E
1. **Playwright setup** (4 horas)
   - Instalar y configurar Playwright
   - Crear `tests/e2e/` estructura
   - Page objects para reutilización

2. **Tests críticos** (6 horas)
   - Flujo completo: login → lección → simulación → completar
   - Edge cases: desconexión, timeouts
   - Validación de datos no persistidos en sandbox

#### Día 3: CI con Postgres
3. **Docker compose Postgres** (2 horas)
   - `docker-compose.postgres.yml`
   - Variables de entorno para CI

4. **GitHub Actions** (4 horas)
   - Actualizar `.github/workflows/test.yml`
   - Matrix con SQLite y Postgres
   - Job separado para E2E tests

#### Día 4: Concurrency Tests
5. **Tests de concurrencia** (4 horas)
   - Habilitar test marcado con skip
   - Validar atomicidad en Postgres
   - Load testing básico

### Entregables
- Suite E2E completa
- CI con Postgres funcional
- Tests de concurrencia habilitados

### Criterios de Aceptación
- ✅ E2E tests cubren flujo crítico
- ✅ CI pasa con Postgres y SQLite
- ✅ Concurrency test pasa sin race conditions
- ✅ Tests corren en <10 min

---

## FASE 7 — Hardening y Deploy (1-2 días)
**Prioridad**: CRÍTICA
**Responsable**: DevOps + Dev Lead

### Objetivos
- Sistema production-ready
- Runbooks y procedimientos
- Monitoring básico

### Tareas Concretas

#### Día 1: Hardening
1. **Security review** (3 horas)
   - Permisos y roles
   - Sanitización de inputs
   - Rate limiting en APIs

2. **Performance** (2 horas)
   - Índices de DB optimizados
   - Caching de contenido estático
   - Lazy loading de lecciones

3. **Logging y monitoring** (1 hora)
   - Logs estructurados
   - Alertas básicas

#### Día 2: Deploy
4. **Runbook** (2 horas)
   - Procedimiento de deploy
   - Rollback plan
   - Smoke tests post-deploy

5. **Staging deploy** (2 horas)
   - Deploy a staging
   - Ejecutar smoke tests
   - Validación manual

6. **Production deploy** (2 horas)
   - Deploy controlado
   - Monitoring post-deploy
   - Validación métricas

### Entregables
- Sistema hardened
- Runbook completo
- Deploy exitoso a producción

### Criterios de Aceptación
- ✅ Security scan sin issues críticos
- ✅ Performance acceptable (<2s load time)
- ✅ Staging tests pasan
- ✅ Production deploy sin downtime
- ✅ Smoke tests post-deploy OK

---

## Cronograma de Sprints

### Sprint 1 (5 días): Fundación
- Fase 0: Preparación
- Fase 1: Admin y contenido
- Inicio Fase 2: Sandbox

### Sprint 2 (5 días): Core Backend
- Completar Fase 2: Sandbox
- Fase 3: APIs REST
- Inicio Fase 4: Frontend

### Sprint 3 (5 días): Frontend y UX
- Completar Fase 4: Frontend UX
- Fase 5: Replay y analítica

### Sprint 4 (5 días): Testing y Deploy
- Fase 6: Tests E2E y CI
- Fase 7: Hardening y deploy

---

## Recursos y Dependencias

### Equipo Mínimo
- **Backend Developer**: Fases 1, 2, 3, 5
- **Frontend Developer**: Fase 4
- **QA Engineer**: Fase 6
- **DevOps**: Fase 7
- **Content Editor**: Fase 1 (contenido demo)

### Herramientas Requeridas
- Docker y Docker Compose
- Playwright para E2E tests
- PostgreSQL para CI
- GitHub Actions (ya configurado)

### Riesgos y Mitigaciones
1. **Complejidad del sandbox**: Mitigación con tests exhaustivos
2. **Performance del frontend**: Mitigación con lazy loading
3. **Contenido demo insuficiente**: Mitigación con generación automática
4. **Integración E2E compleja**: Mitigación con setup incremental

---

## Métricas de Éxito

### Técnicas
- Tests coverage >90%
- E2E tests <10 min execution
- API response time <500ms
- Zero critical security issues

### Producto
- Editor puede crear lección en <10 min
- Usuario completa simulación en <5 min
- Tasa de completación >70%
- Mobile usability score >85

### Operacionales
- Deploy sin downtime
- Rollback en <5 min si necesario
- Monitoring y alertas funcionales
- Runbook completo y testado

---

## Comandos de Referencia Rápida

```powershell
# Setup inicial
git checkout -b feature/academy-launch
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Tests rápidos
$env:DJANGO_SETTINGS_MODULE='core.test_settings'
python manage.py test empresa.tests -q

# Contenido demo
python manage.py crear_contenido_demo

# E2E tests
playwright install
pytest tests/e2e -q

# CI local con Postgres
docker compose -f docker-compose.postgres.yml up -d
python manage.py migrate
python manage.py test
```

Este plan está diseñado para ser ejecutable, medible y adaptable según el progreso del equipo.