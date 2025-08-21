# Academia CONTAFY — Roadmap completo y guía práctica

Este documento centraliza todas las fases, pasos y comandos necesarios para convertir la funcionalidad actual en una "Academia" estilo Duolingo, adaptada por tipo de empresa (comercial, manufactura, servicios). Está pensado como guía operativa y técnica para desarrolladores, QA y operadores.

Fecha: 2025-08-14

---

## Nombre del archivo
- `ACADEMIA_README.md` (este archivo)

---

## Resumen ejecutivo (1 frase)
Guía técnica y operativa para completar la Academia CONTAFY: micro-lecciones, prácticas guiadas, simulaciones sandbox, personalización, authoring, métricas y despliegue.

## Checklist inicial (qué contiene este README)
- Fases funcionales y técnicas faltantes (MVP → escala).
- Para cada fase: objetivo, criterios de éxito, contrato (endpoints), cambios de código/DB/templates, tests mínimos, edge cases y pasos de despliegue.
- Comandos y ejemplos (PowerShell/Heroku) para migraciones, seed y pruebas.
- Roadmap priorizado y artefactos a crear.

---

## Fase 0 — Estado actual (premisas)
- Código base: Django (vistas, templates), modelos en `empresa/models_aprendizaje.py`.
- Ya implementado: `leccion.pasos` en código (migración manual `0008_add_pasos_field.py` en repo), vista `leccion_detalle`, plantilla `leccion_interactiva.html`, endpoint `paso_completado` para micro‑XP (añadido en workspace), `GamificacionService` presente.
- Bloqueo actual: aplicar migraciones y correr seed en un entorno con DB accesible (Heroku recomendado).

---

## Fase 1 — Micro‑lecciones y micro‑XP (MVP)

Objetivo
- Micro‑lecciones con pasos (paso por paso), marcado por usuario y otorgamiento inmediato de micro‑XP.

Criterios de éxito
- Usuario marca pasos y recibe XP.
- Prevención básica de doble conteo (session-based).
- Perfil y estadísticas reflejan XP actualizado.

Contrato del endpoint principal
- POST `/empresa/aprendizaje/paso-completado/`
  - Input JSON: `{ "leccion_id": int, "paso_index": int, "micro_xp"?: int }`
  - Auth: sesión (login_required)
  - Output 200: `{ ok: true, resultado: { xp_otorgada, xp_total, nivel_actual }, intentos }`
  - Errores: 400/404/401 con mensaje

Cambios clave (ya aplicados o pendientes)
- Modelos: `Leccion.pasos` (JSONField/TextField) — migración en repo `empresa/migrations/0008_add_pasos_field.py` (aplicar).
- Views: `paso_completado` (validación, otorgar XP, session key) — añadido.
- Templates: `empresa/templates/empresa/aprendizaje/leccion_interactiva.html` — botones por paso y llamada a endpoint — actualizado.
- Scripts: `scripts/seed_demo_leccion.py` — crear demo de lección con pasos.

Tests mínimos
- Unit tests para endpoint: éxito, duplicado, out-of-range, auth required.
- Integration: flujo abrir lección -> marcar paso -> verificar `PerfilAprendizaje.xp_total`.

Edge cases
- Paso index inválido / `pasos` malformado.
- Reintentos multi-dispositivo (session-based no basta). Mitigar con server-side dedupe y límites por IP.

Pasos detallados para completar
1. Aplicar migraciones en entorno con DB:
```powershell
# En Heroku (reemplaza your-app-name)
heroku git:remote -a your-app-name
git push heroku main
heroku run python manage.py migrate --app your-app-name
heroku run python scripts/seed_demo_leccion.py --app your-app-name
```
2. Probar manualmente la lección interactiva y marcar pasos.
3. Añadir tests en `empresa/tests/test_aprendizaje.py` y ejecutar CI.

---

## Fase 2 — Simulaciones Sandbox integradas

Objetivo
- Permitir que pasos de práctica lancen simulaciones de venta/receta/servicio en modo sandbox y que el resultado otorgue XP/feedback.

Criterios de éxito
- Simulaciones ligadas a `SimulacionUsuario` con `sandbox=True`.
- Resultados devuelven puntuación y pueden aumentar XP.

Contrato/Endpoints
- Extender `POST /aprendizaje/simulacion/venta/` y equivalentes para aceptar `sandbox` y `leccion_id`.
- `POST /aprendizaje/paso-completado/` puede retornar `simulacion_id` si solicita iniciar simulación.

Cambios necesarios
- `SimulacionUsuario` model: añadir `sandbox` boolean.
- `SimulacionService`: soportar sandbox (no afectar datos reales, usar transacción/revert o DB de pruebas).
- UI: modal para simulación con datos de ejemplo.

Pruebas
- Unit: iniciar simulación sandbox no modifica entidades reales.
- Integration: completar simulación y recibir XP.

Pasos detallados
1. Crear migración para `SimulacionUsuario.sandbox`.
2. Implementar lógica sandbox en `SimulacionService`.
3. UI modal + endpoint.

---

## Fase 3 — Motor de personalización y recomendaciones

Objetivo
- Recomendar la siguiente lección según tipo de empresa y rendimiento (heurísticas → ML).

Datos y contratos
- Registrar `EventoAprendizaje` por cada interacción (step_completed, lesson_completed, simulation_result, quiz_answer).
- Servicio `RecommendationService.predict_next_leccion(usuario)`.

Plan
1. Instrumentar eventos en DB.
2. Implementar heurísticas (cold-start: tipo_empresa defaults).
3. Recolectar datos y entrenar modelo offline.
4. Desplegar modelo con endpoint o como librería.

---

## Fase 4 — Authoring / CMS de lecciones

Objetivo
- Panel para crear módulos/lecciones/pasos/quizzes y previsualización.

Requisitos
- JSON schema para `pasos`.
- Editor (ACE/Monaco) en admin o un micro-front para authoring.

Pasos
1. Añadir `docs/pasos_schema.json` y validación en backend.
2. Implementar editor y preview endpoint.

---

## Fase 5 — Gamificación avanzada y social

Qué incluir
- Ligas semanales, tablas, retos entre empleados, compartir logros.

Acciones
1. Extender `GamificacionService` con ligas.
2. UI: timeline, compartir, reto UI.

---

## Fase 6 — QA, pruebas y CI/CD

Tests recomendados
- Unit tests para views y servicios.
- Integration tests para flujos críticos.
- E2E (Playwright/Selenium) para recorrido usuario.

CI/CD
- Pre-merge: lint, pytest, build.
- Despliegue staging automático y migraciones manuales aprobadas para prod.

Comandos rápidos
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py test
python scripts/seed_demo_leccion.py
```

---

## Fase 7 — Observabilidad y métricas

Eventos a rastrear
- `step_completed`, `lesson_completed`, `simulation_started`, `simulation_result`, `quiz_answer`.

Dashboards
- Crear en Metabase/Redash: retención D1/D7, tiempo medio, pasos completados, XP diario.

---

## Fase 8 — Seguridad, cumplimiento y escalado

Recomendaciones
- Rate limiting, logs centralizados (ELK), backups, revisiones de migraciones.
- Auditoría de datos (GDPR/local) y SSO si es necesario.

---

## Roadmap prioritario (sprints)
- Sprint 1 (1–2w): Fase 1 completada, migraciones aplicadas, seed y tests.
- Sprint 2 (2–3w): Fase 2 MVP (sandbox básico).
- Sprint 3 (3–4w): Authoring y validación de contenidos.
- Sprint 4+: Personalización, ML offline y escalado.

---

## Artefactos a crear/actualizar en repo
- `empresa/migrations/0008_add_pasos_field.py` (ya presente)
- `scripts/seed_demo_leccion.py` (ya presente)
- `docs/pasos_schema.json` (nuevo)
- `docs/ACADEMIA_README.md` (este archivo)
- `empresa/tests/test_aprendizaje.py` (nuevo)

---

## Próximos pasos inmediatos (elige uno)
1. Aplicar migraciones y correr seed en Heroku (comandos arriba).  
2. Escribir tests unitarios/integración mínimos para `paso_completado` (puedo generarlos).  
3. Preparar cambios y migraciones para `SimulacionUsuario.sandbox`.

---

Si quieres que añada este archivo al repo (ya lo hice) y genere los tests o scripts de migración adicionales, dime cuál de las tres acciones quieres que haga ahora (1, 2 o 3) y procedo.
