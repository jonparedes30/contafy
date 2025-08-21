# Convertir la Academia CONTAFY en una experiencia tipo Duolingo

Este documento contiene una guía completa, paso a paso, de lo que falta y cómo implementarlo para transformar el actual subsystema de aprendizaje (micro-lecciones + simulaciones) en una experiencia formativa tipo Duolingo: lecciones cortas, práctica gamificada, progresión por rutas, simulaciones sandbox y métricas.

Está pensado como un plan técnico y operativo que un equipo de ingeniería/QA/UX puede usar para ejecutar los cambios y pruebas.

---

## Objetivo

Tener un apartado "Academia" que ofrezca:
- Rutas y módulos organizados por tipo de empresa (como Duolingo: unidades → lecciones → pasos).
- Micro-lecciones con pasos prácticos, quizzes y micro‑XP por paso.
- Simulaciones sandbox (venta/receta/servicio) integradas en las lecciones con escenarios predefinidos.
- Gamificación: XP, niveles, insignias, logros, actividad diaria.
- UI responsiva y accesible, feedback inmediato (toasts, modal, animaciones ligeras).
- Seguimiento, métricas y telemetría para AB testing y mejora continua.

---

## Resumen del estado actual (breve)
- Backend: modelos de lecciones, progreso y simulaciones ya existen (`empresa.models_aprendizaje`, `empresa.models_simulaciones`).
- Servicios: `GamificacionService`, `SimulacionService` implementados.
- Frontend: plantilla `leccion_interactiva.html` con JS inline (ahora extraído a `static/empresa/js/aprendizaje.js`), modal para simulación, marcadores de pasos y toasts.
- Tests: suite de tests unitarios para APIs y simulaciones; se ejecutan con `core.test_settings` (SQLite). Concurrency test marcado para Postgres.

---

## Lista priorizada de procesos/módulos faltantes (alto → bajo)

1. Infraestructura de contenido (CRU de lecciones/escenarios) en Admin
2. Rutas/perspectivas adaptativas (sistema de desbloqueo y adaptivity)
3. UI/UX estilo "lección por pasos" (mejoras: animaciones, micro-feedback, review cards)
4. Simulación en‑UI completa (modal interactivo, inputs reutilizables, paso a paso)
5. Sistema de replay/recording de simulaciones para analítica
6. Tests end-to-end (Playwright/Selenium) que cubran el flujo completo del alumno
7. CI con Postgres (test matrix) y run del concurrency test
8. Telemetría y métricas (event tracking, KPIs: retención, completación, avg score)
9. Localización y accesibilidad (WCAG)
10. Contenido editorial pipeline (CSV/Markdown import, versionado de lecciones)

---

## Implementación detallada por área

A continuación cada área con pasos concretos, archivos a tocar y ejemplos.

### 1) Contenido y Admin (obligatorio)
Objetivo: permitir a los editores crear/modificar módulos, lecciones, pasos y escenarios sin tocar código.

Pasos:
- Revisar `empresa.models_aprendizaje` y `empresa.models_simulaciones`. Asegurar que todos los campos necesarios están modelados (title, slug, orden, tipo_empresa, pasos JSON, puntos_xp, tiempo_estimado, dificultad, visible/activo).
- Añadir `ModelAdmin` amigable en `empresa/admin.py` para `ModuloAprendizaje`, `Leccion`, `EscenarioSimulacion`, `TipoSimulacion` con inline editors para pasos (usar `django-json-widget` o `TabularInline` con TextField).
- Añadir validaciones en `clean()` de los modelos (por ejemplo, steps JSON well-formed, no pasos vacíos).
- Crear comandos de management para cargar contenido demo y escenarios (`manage.py crear_contenido_demo`).

Archivos a editar:
- `empresa/admin.py`
- `empresa/models_aprendizaje.py` (si hay campos faltantes)
- Crear `management/commands/crear_contenido_demo.py`

### 2) Rutas, desbloqueo y adaptivity (alto)
Objetivo: que las rutas se adapten al rendimiento del usuario (p. ej. si falla quiz, repetir pasos o proponer revisión).

Pasos:
- Implementar en `ProgresoUsuario` campos: `ultima_fecha`, `nivel_actual`, `ultimas_respuestas` (estadísticas básicas).
- Implementar `RecomendationService` simple que, al completar una lección o simulación, calcule la siguiente lección sugerida según: nivel, tipo_empresa, puntuación en quizzes.
- En UI, mostrar un panel "Siguiente recomendada" dentro del dashboard de `aprendizaje`.

Archivos a editar:
- `empresa/models_aprendizaje.py` (migraciones)
- `empresa/services/recomendation_service.py` (nuevo)
- `empresa/views/aprendizaje.py` (exponer recomendación al template)

### 3) Frontend experiencia tipo Duolingo (alto)
Objetivo: UX por pasos claros, micro-feedback, animaciones sutiles y transiciones.

Pasos concretos:
- Extraer todo el JS a `static/empresa/js/aprendizaje.js` (ya hecho) y testear en distintos browsers.
- Reemplazar `mostrarToast` con Bootstrap Toasts (ya integrado) y añadir micro-animations para pasos completados.
- Añadir revisión por tarjetas: cuando el usuario falla un quiz o simulación, mostrar "revisión" con explicación.
- Añadir sistema de streaks y actividad diaria visible en `perfil_usuario`.

UI Files:
- `empresa/templates/empresa/aprendizaje/leccion_interactiva.html` (data attributes + componentes)
- `static/empresa/js/aprendizaje.js` (logic)
- `static/empresa/css/aprendizaje.css` (opcional)

### 4) Simulación interactiva (medio‑alto)
Objetivo: dar al alumno un sandbox interactivo dentro del modal o página anexa, no solo iniciar y mostrar JSON.

Pasos:
- Añadir UI dentro del modal: inputs dinámicos según `EscenarioSimulacion.datos_iniciales` (pre-fill), formularios validados client-side.
- Añadir endpoints para guardar pasos intermedios (autosave) y para recuperar simulación por id.
- Implementar WebSocket (Django Channels) para simulaciones colaborativas o feedback en tiempo real (opcional).

APIs necesarias:
- `GET /aprendizaje/simulacion/<id>/` → recuperar estado
- `POST /aprendizaje/simulacion/<id>/guardar/` → guardar avance
- `POST /aprendizaje/simulacion/<id>/finalizar/` → procesar y otorgar XP

### 5) Replay + Analítica (medio)
Objetivo: almacenar las acciones del usuario dentro de la simulación para poder reproducir/revisar y mejorar contenido.

Pasos:
- Añadir `SimulacionEvento` model con FK a `SimulacionUsuario`, timestamp, tipo, payload.
- Durante la simulación el frontend envía eventos (JSON) vía AJAX o WebSocket.
- Interfaz en admin para reproducir eventos y exportarlos (CSV/JSON).

### 6) Tests End-to-End y QA (alto)
Objetivo: validar comportamiento completo del flujo alumno.

Pasos:
- Añadir Playwright tests (recomendado) o Selenium.
- Tests a cubrir:
  - Flujos de lección: abrir lección, marcar pasos, iniciar simulación, completar simulación, marcar lección completa.
  - Edge cases: desconexión, inválidos, reintentos.
- Integrar los e2e en CI (job separado con docker-compose postgres + headless browser).

Ejemplo comando local (PowerShell):

```powershell
# Levantar Postgres en Docker
docker compose -f docker-compose.postgres.yml up -d
# Instalar deps
pip install -r requirements.txt
$env:DJANGO_SETTINGS_MODULE='core.test_settings'; python manage.py migrate
# Ejecutar Playwright tests (si están instalados)
playwright install
pytest tests/e2e -q
```

### 7) CI con Postgres y concurrency (obligatorio para validar atomicidad)
Objetivo: ejecutar tests unitarios y concurrency test contra Postgres en CI.

Pasos:
- Ya existe `.github/workflows/test.yml` base. Actualizar para que `DJANGO_SETTINGS_MODULE` apunte a un settings que use `DATABASE_URL` env var o a `core.ci_settings` que configure Postgres.
- Incluir matrix con `python-version` y `DJANGO_SETTINGS_MODULE` si aplica.
- Asegurar job que corre `python manage.py test empresa.tests.test_paso_concurrency.PasoConcurrencyTests.test_concurrent_mark_same_paso` sin skip.

Ejemplo fragmento GitHub Actions (ya agregado en repo):
- Añadir `run: python manage.py test empresa.tests` y garantizar migraciones.

### 8) Telemetría y KPIs (medio)
Objetivo: instrumentar eventos para analizar retención y efectividad.

Eventos recomendados:
- step.completed (user_id, leccion_id, paso_index, tiempo, xp)
- simulacion.started, simulacion.completed (simulacion_id, tipo, puntos)
- quiz.attempt (pregunta_id, correcta)

Implementación:
- Guardar eventos en DB y duplicar a un sistema de colas (Kafka/Rabbit) para pipeline analítico.
- Dashboard ETS: Grafana o Metabase para métricas: tasa de completación, NPS por lección, tiempo medio.

### 9) Localización (i18n) y accesibilidad (a11y) (bajo)
Pasos:
- Exportar strings con `django-admin makemessages` y traducir.
- Revisar ARIA attributes en modals, buttons y toasts.
- Test con Lighthouse y axe-core.

### 10) Contenido pipeline (bajo)
Pasos:
- Definir un formato de import (CSV/Markdown/JSON) para lecciones y escenarios.
- Crear `management/commands/import_lecciones.py`.
- Versionado con git (cada cambio de contenido puede generar un commit en branch `content/*`).

---

## Comandos y entorno local recomendados

1) Ejecutar tests rápidos con SQLite (rápido):

```powershell
$env:DJANGO_SETTINGS_MODULE='core.test_settings'; python -m pip install -r requirements.txt; python manage.py test empresa.tests; Remove-Item Env:\DJANGO_SETTINGS_MODULE
```

2) Levantar Postgres local (docker-compose)

Crear `docker-compose.postgres.yml` (ejemplo mínimo):

```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: contafy_test
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - '5432:5432'
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Luego en PowerShell:

```powershell
docker compose -f docker-compose.postgres.yml up -d
$env:DJANGO_SETTINGS_MODULE='core.ci_settings'
# core.ci_settings debe leer DATABASE_URL o configurar DB a postgres://postgres:postgres@localhost:5432/contafy_test
python manage.py migrate
python manage.py test empresa.tests
Remove-Item Env:\DJANGO_SETTINGS_MODULE
```

3) Ejecutar el test de concurrencia específico (Postgres required)

```powershell
$env:DJANGO_SETTINGS_MODULE='core.ci_settings'; python manage.py test empresa.tests.test_paso_concurrency.PasoConcurrencyTests.test_concurrent_mark_same_paso -q; Remove-Item Env:\DJANGO_SETTINGS_MODULE
```

---

## Recomendaciones de arquitectura y rendimiento
- Poner índices en columnas usadas en filtros (usuario, leccion, fecha) para escalabilidad.
- Purgar logs de simulaciones antiguas o mover a almacenamiento frío para que la DB no crezca sin control.
- Cachear metadatos (tipos de simulación, escenarios activos) en Redis para reducir latencia de templates.
- Limitar tamaño de `datos_entrada` JSON y validar esquema con `jsonschema` en backend.

---

## Plan de trabajo sugerido (4 sprints ejemplo)
- Sprint 1: Admin y content pipeline; tests unitarios; CI Postgres básico
- Sprint 2: Frontend UX polish (toasts, modal interactivo), simulación autosave
- Sprint 3: Replays, analítica básica, E2E tests
- Sprint 4: Adaptivity, AB testing, pulido y accesibilidad

---

## Estimaciones (muy aproximadas)
- Admin + content pipeline: 3-5 días
- Frontend UX + modal interactivo: 5-10 días
- E2E tests + CI robusto: 3-5 días
- Telemetría + replay: 5-8 días
- Adaptivity/AI recommendations: 5-10 días

---

## Siguientes pasos inmediatos que puedo ejecutar aquí
- (A) Crear `core.ci_settings` que use `DATABASE_URL` para CI y ajustar `.github/workflows/test.yml` (recomendado)
- (B) Generar `docker-compose.postgres.yml` en repo con ejemplos y scripts para ejecutar local tests
- (C) Crear `management/commands` para cargar contenido demo y escenarios

Dime cuál quieres que aplique primero (A/B/C) y lo implemento.
