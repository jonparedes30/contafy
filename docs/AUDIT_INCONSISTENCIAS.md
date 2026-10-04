# Auditoría de Inconsistencias Visuales — Contafy

> **Versión:** 1.0 — 2026-05-21
> **Referencia base:** [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md)
> **Objetivo:** Roadmap accionable para alinear los templates del sistema con la identidad visual de la landing page.

Este documento lista cada inconsistencia detectada con su archivo, línea, problema específico y corrección sugerida. Es un mapa de refactor incremental — cada fila puede convertirse en un PR/commit separado.

---

## Resumen ejecutivo

| Métrica | Valor |
|---|---|
| Templates auditados | 26+ |
| Templates fuera de marca | **18 (69%)** |
| Templates con `<style>` blocks >20 líneas | **26** |
| Gradientes púrpura/magenta detectados | 8 templates |
| Templates con tipografía Arial aislada | 1 (`entrada_beta.html`) |
| Templates con Font Awesome mezclado con Bootstrap Icons | 26+ |
| Templates con Chart.js fuera de paleta brand | 5 |
| Templates con tablas inconsistentes | 31 |
| Templates con modales sin color de marca | 20+ (136 modales totales) |
| Usos de SweetAlert/alerts | 65+ |

---

## 1. Tabla priorizada por impacto

| Prioridad | Template | Problema | Línea(s) | Corrección sugerida |
|---|---|---|---|---|
| 🔴 Alta | `entrada_beta.html` | Arial + colores aislados (#2c3e50) | 8 | Migrar a `base_auth.html` + design system |
| 🔴 Alta | `crear_empleado.html` | Gradiente púrpura `#667eea → #764ba2` | 173 | Usar `--grad-brand` |
| 🔴 Alta | `dashboards/dashboard_basico.html` | Gradiente multicolor caótico `#667eea, #764ba2, #f093fb, #f5576c` | 198 | `--grad-brand` o `--grad-hero-bg` |
| 🔴 Alta | `login.html` | Header verde-gris aislado `#27ae60 → #2c3e50` | 12 | Usar `--grad-brand` |
| 🟡 Media | `registro.html` | Gradiente condicional verde-gris vs brand | 24 | `--grad-brand` siempre, no condicional |
| 🟡 Media | `mi_empresa.html` | Verde Bootstrap `#28a745 → #20c997` | 264 | `--grad-brand` |
| 🟡 Media | `mobile_base.html` | Verde-gris `#27ae60 → #2c3e50` | 25 | `--grad-brand` |
| 🟡 Media | `dashboards/dashboard_ventas.html` | Gradiente animado multicolor `-45deg` | varias | `--grad-brand` |
| 🟡 Media | `dashboards/dashboard_gastos.html` | Gradiente animado multicolor | varias | `--grad-brand` |
| 🟡 Media | `dashboards/dashboard_inventario.html` | Gradiente animado multicolor | varias | `--grad-brand` |
| 🟡 Media | `agente_ia.html` | 104 líneas CSS inline + gradientes random | 9-112 | Mover a `clean_enterprise.css` + `--grad-brand` |
| 🟢 Baja | `crear_venta.html` | Colores Bootstrap inline (#198754, #16a34a) | 117-136 | Usar variables `--c-green` |
| 🟢 Baja | `asistente_ayuda.html` | Gradiente verde Bootstrap `#28a745 → #20c997` | varias | `--grad-brand` |
| 🟢 Baja | `exportaciones_comercio.html` | Azul Bootstrap `#007bff → #0056b3` | varias | `--grad-brand` o `--c-blue` |
| 🟢 Baja | `exportaciones_manufactura.html` | Verde Bootstrap `#28a745 → #20c997` | varias | `--grad-brand` |
| 🟢 Baja | `listar_empresas.html` | Turquesa `#4ecdc4 → #45b7d1` | varias | `--c-teal` + `--c-blue` |
| 🟢 Baja | `reporte_ia.html` | Gradiente púrpura | varias | `--grad-brand` |
| 🟢 Baja | `crear_venta.html` (continuación) | Colores `#198754` y `#16a34a` hardcoded | 118-119 | `var(--c-green)` y `var(--c-green-d)` |

---

## 2. Patrones a aplicar masivamente (find & replace)

Estos reemplazos pueden ejecutarse en bloque con un buen script o regex global:

```bash
# Colores hardcodeados → variables
sed -i 's/#667eea/var(--c-blue)/g' empresa/templates/empresa/**/*.html
sed -i 's/#764ba2/var(--c-blue-d)/g' empresa/templates/empresa/**/*.html
sed -i 's/#27ae60/var(--c-green)/g' empresa/templates/empresa/**/*.html
sed -i 's/#28a745/var(--c-green)/g' empresa/templates/empresa/**/*.html
sed -i 's/#20c997/var(--c-teal)/g' empresa/templates/empresa/**/*.html
sed -i 's/#007bff/var(--c-blue)/g' empresa/templates/empresa/**/*.html
sed -i 's/#0056b3/var(--c-blue-d)/g' empresa/templates/empresa/**/*.html
sed -i 's/#198754/var(--c-green-d)/g' empresa/templates/empresa/**/*.html
```

**⚠️ Pre-condición:** definir todas las variables CSS en `clean_enterprise.css` antes de ejecutar.

### Gradientes específicos a reemplazar:

| Patrón antiguo | Patrón nuevo |
|---|---|
| `linear-gradient(135deg, #27ae60 0%, #2c3e50 100%)` | `var(--grad-brand)` |
| `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` | `var(--grad-brand)` |
| `linear-gradient(45deg, #28a745, #20c997)` | `var(--grad-brand)` |
| `linear-gradient(135deg, #007bff 0%, #0056b3 100%)` | `var(--grad-brand)` |
| `linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #f5576c)` | `var(--grad-hero-bg)` |
| `font-family: Arial, sans-serif;` | Eliminar (heredar de base_auth.html) |

---

## 3. Plan de migración recomendado

### Fase 1 — Cimientos (sin tocar templates)
**Objetivo:** Centralizar variables y reglas globales.

- [ ] Copiar variables `:root` de `landing.html` al inicio de `clean_enterprise.css`
- [ ] Agregar reglas globales para `.alert`, `.form-control`, `.table.contafy-table`, `.modal-content`, `.pagination`, `.tooltip-inner`, `.dropdown-menu`, `.spinner-border`, `.breadcrumb`
- [ ] Crear `_components/empty_state.html` reutilizable
- [ ] Crear (futuro) `empresa/static/js/contafy_charts.js` con `CONTAFY_CHART_COLORS` y `CONTAFY_CHART_DEFAULTS`

### Fase 2 — Alta prioridad
Templates de **autenticación + dashboards principales** que el usuario ve frecuentemente:

- [ ] `entrada_beta.html` — eliminar CSS aislado, migrar a `base_auth.html`
- [ ] `login.html` — `--grad-brand` en header
- [ ] `registro.html` — eliminar gradiente condicional, usar `--grad-brand`
- [ ] `crear_empleado.html` — eliminar gradiente púrpura
- [ ] `dashboards/dashboard_basico.html` — eliminar gradiente multicolor

### Fase 3 — Media prioridad
- [ ] `dashboards/dashboard_ventas.html`
- [ ] `dashboards/dashboard_gastos.html`
- [ ] `dashboards/dashboard_inventario.html`
- [ ] `dashboards/dashboard_metas.html`
- [ ] `dashboards/dashboard_productos.html`
- [ ] `mi_empresa.html`
- [ ] `mobile_base.html`
- [ ] `agente_ia.html` — extraer CSS a global

### Fase 4 — Baja prioridad
- [ ] `crear_venta.html` — limpiar inline colors
- [ ] `crear_compra.html`
- [ ] `crear_producto.html`
- [ ] `asistente_ayuda.html`
- [ ] `exportaciones_comercio.html`
- [ ] `exportaciones_manufactura.html`
- [ ] `listar_empresas.html`
- [ ] `reporte_ia.html`

### Fase 5 — Componentes transversales
- [ ] Tablas — aplicar clase `.contafy-table` en 31 listados
- [ ] Modales — añadir gradiente brand a headers en 20 templates
- [ ] Swal — estandarizar `customClass` y `buttonsStyling: false` en 65+ usos
- [ ] Tooltips — inicialización global en `base.html`
- [ ] Empty states — usar `_components/empty_state.html` donde aplique

---

## 4. Auditoría detallada por tema

### 4.1 Gráficos (Chart.js) — 5 templates

| Template | Problema en gráfico | Línea(s) | Corrección |
|---|---|---|---|
| `dashboard.html` | Colores Material `rgba(76,175,80)`, `rgba(244,67,54)` + tooltip navy con border verde Material | 475, 484, 504-507 | Usar `CONTAFY_CHART_COLORS.income/expense` + `CONTAFY_CHART_DEFAULTS` |
| `comparacion_sector.html` | Radar con paleta arbitraria | 271+ | Usar `CONTAFY_CHART_COLORS.palette[0..N]` |
| `flujo_caja.html` | Line chart sin defaults consistentes (fonts, grid color) | 230+ | Aplicar `CONTAFY_CHART_DEFAULTS` completo |
| `valuacion.html` | Configuración minimal, sin tooltip estandarizado | 207+ | Aplicar `CONTAFY_CHART_DEFAULTS` |
| `_components/_grafico_tendencias.html` | Componente reutilizable — usar como referencia base, alinear colores | - | Verificar y armonizar con `CONTAFY_CHART_COLORS` |

**Reemplazos comunes en todos los gráficos:**

```js
// ANTES
rgba(76, 175, 80, X)   →  rgba(16, 185, 129, X)   // verde Material → brand
rgba(244, 67, 54, X)   →  rgba(239, 68, 68, X)    // rojo Material → brand
rgba(44, 62, 80, X)    →  rgba(15, 23, 42, X)     // navy oscuro → brand
font: {} (default)     →  font: { family: 'Inter' }
tooltip: {} (default)  →  tooltip: CONTAFY_CHART_DEFAULTS.plugins.tooltip
```

### 4.2 Tablas — 31 templates

**Problemas detectados:**
- Mezcla de `table-striped` y `table-hover` sin criterio
- Headers con diferentes pesos y colores entre listados
- Filas vacías sin empty-state estandarizado
- Algunos `table-bordered` (genera ruido visual)

**Templates afectados (lista parcial):**
- `listar_ventas.html`
- `listar_compras.html`
- `listar_productos.html`
- `listar_gastos.html`
- `listar_capital.html`
- `listar_cuentas_contables.html`
- `inventario.html`
- `gestion_deudas.html`
- `actividad_reciente.html`
- `historial_meta.html`
- `metas.html`
- `manufactura/listar_*.html` (varios)

**Acción:** Reemplazar `<table class="table table-striped">` por `<table class="table contafy-table table-hover align-middle">` y aplicar reglas globales de `.contafy-table` (ver sección 9 de DESIGN_SYSTEM.md).

### 4.3 Modales — 136 ocurrencias en 20 templates

**Problemas detectados:**
- 80%+ usan modal header sin color de marca (gris/blanco Bootstrap default)
- Algunos modales con `style="background: ..."` inline con colores arbitrarios
- `border-radius` heterogéneo (Bootstrap default 0.5rem vs custom)

**Templates con más modales:**
| Template | # modales |
|---|---|
| `mi_empresa.html` | 21 |
| `crear_venta.html` | 18 |
| `crear_producto.html` | 15-17 |
| `crear_compra.html` | 15 |
| `gestion_deudas.html` | 15 |
| `manufactura/dashboard.html` | varios |

**Acción:** Aplicar gradiente brand en headers de modales informativos, color sólido danger/success/warning en modales semánticos. Override CSS global: `.modal-content { border-radius: 16px; }`.

### 4.4 Alertas / SweetAlert — 65+ usos

**Problemas detectados:**
- Colores de botones Swal hardcoded sin usar variables de marca
- Algunos usan `confirmButtonColor: '#28a745'` (Bootstrap) en lugar de `#10b981` (brand)
- Mezcla de `Swal.fire`, `alert()` nativo y `.alert` Bootstrap inline
- Falta de `customClass` para coherencia visual

**Templates con uso intenso:**
- `crear_producto.html` (17 usos)
- `crear_compra.html` (11)
- `crear_venta.html` (10)
- `comparacion_sector.html` (4)
- `asistente_ayuda.html` (3)

**Acción:**
1. Crear helper global `static/js/contafy_swal.js` con configuración estándar
2. Reemplazar `confirmButtonColor: '#28a745'` → `confirmButtonColor: '#10b981'`
3. Añadir `customClass: { confirmButton: 'btn btn-primary', cancelButton: 'btn btn-outline-secondary' }` + `buttonsStyling: false`

### 4.5 Formularios — Inputs y validaciones

**Problemas detectados:**

| Inconsistencia | Templates afectados |
|---|---|
| Marcador `*` rojo en required vs literal "(opcional)" vs nada | `crear_capital.html`, `crear_empleado.html`, `crear_producto.html`, `crear_empresa.html`, `crear_cuenta_contable.html` |
| Date inputs: mezcla de `type="date"`, flatpickr, daterangepicker | varios listados con filtros de fecha |
| Inline `style="text-align: right"` en lugar de `class="text-end"` | crear_venta, crear_compra |
| Validaciones: Bootstrap `.is-invalid` vs `.text-danger small` custom | registro, login, crear_empleado |

**Acción:**
1. Convención: SOLO marcar required con `*` rojo después del label
2. Estandarizar date inputs en `type="date"` con input-group + icon `bi-calendar3`
3. Reemplazar styles inline con clases Bootstrap utility
4. Validaciones: usar `.is-invalid` + `.invalid-feedback` siempre

### 4.6 Sidebar / Topbar

**Problemas detectados:**
- `mobile_base.html` duplica estilos del sidebar con colores aislados (`#27ae60 → #2c3e50`)
- Algunos templates añaden `<style>` que sobrescribe sidebar (rompe la consistencia)
- Templates como `dashboard.html` agregan estilos inline al topbar

**Acción:**
- Eliminar `<style>` blocks que tocan `.sidebar` o `.topbar` en templates individuales
- Centralizar TODO el styling en `base.html` (donde ya está) y `clean_enterprise.css`
- `mobile_base.html` debe extender `base.html` o usar las mismas clases, no duplicar estilos

### 4.7 Tooltips, Paginación, Breadcrumbs

**Problemas detectados:**
- **Tooltips (35 templates):** usan defaults de Bootstrap (gris) en lugar de navy brand
- **Paginación:** `components/pagination.html` existe pero solo se usa en 1-2 templates (resto duplica HTML inline)
- **Breadcrumbs:** solo 3-4 templates los implementan, con separadores y estilos diferentes

**Acción:**
1. Tooltips: inicialización global en `base.html` + override CSS `.tooltip-inner { background: var(--c-navy); }`
2. Paginación: incluir `components/pagination.html` en todos los listados
3. Breadcrumbs: crear componente reutilizable `_components/breadcrumbs.html`

### 4.8 Print / PDF — 3 templates con `@media print`

**Templates afectados:**
- `balance_general.html`
- `estado_resultado.html`
- `reporte_ia.html`

**Problemas:**
- Diferentes reglas de page-break y márgenes
- Cada uno define su propio `.no-print`
- Headers/footers de impresión no estandarizados

**Acción:** Mover reglas `@media print` a `clean_enterprise.css` global con clases `.no-print`, `.print-only`, `@page`, `tr { page-break-inside: avoid; }` aplicables a TODO el sistema.

### 4.9 Iconografía mezclada — 26+ templates

**Problema:**
- 192 instancias de Font Awesome (`fas`, `fa-*`) mezcladas con
- 400+ instancias de Bootstrap Icons (`bi-*`)
- En el mismo archivo: `registro.html` usa ambos en la línea 26

**Templates más afectados por mezcla:**
- `registro.html` — Font Awesome dominante, mezcla `bi-clock` en una línea
- `login.html` — mezcla similar
- `crear_venta.html` — `fa-*` en algunos botones + `bi-*` en otros
- `crear_compra.html` — íconos de Material Design + Bootstrap

**Acción:**
1. Para templates nuevos: solo Bootstrap Icons
2. Para templates legacy: elegir UNA librería por archivo y migrar el resto
3. Migración prioritaria: registro, login, dashboards (los más visibles)

---

## 5. Templates con `<style>` inline >20 líneas (Apéndice)

Estos 26 templates tienen bloques de estilo dentro del HTML que deberían migrar a `clean_enterprise.css`:

| Template | Líneas de `<style>` |
|---|---|
| `agente_ia.html` | 104 |
| `dashboard.html` | 80+ |
| `dashboards/dashboard_basico.html` | 60+ |
| `dashboards/dashboard_ventas.html` | 50+ |
| `dashboards/dashboard_gastos.html` | 50+ |
| `dashboards/dashboard_inventario.html` | 50+ |
| `dashboards/dashboard_productos.html` | 45+ |
| `dashboards/dashboard_metas.html` | 45+ |
| `mi_empresa.html` | 40+ |
| `crear_venta.html` | 35+ |
| `crear_compra.html` | 30+ |
| `crear_producto.html` | 30+ |
| `inventario.html` | 30+ |
| `gestion_deudas.html` | 30+ |
| `reporte_ia.html` | 30+ |
| `comparacion_sector.html` | 25+ |
| `asistente_ayuda.html` | 25+ |
| `listar_empresas.html` | 25+ |
| `flujo_caja.html` | 25+ |
| `balance_general.html` | 25+ |
| `valuacion.html` | 25+ |
| `metas.html` | 25+ |
| `actividad_reciente.html` | 25+ |
| `registro.html` | 25+ |
| `login.html` | 20+ |
| `entrada_beta.html` | 20+ |

**Acción:** identificar selectores únicos por template y moverlos a una sección dedicada en `clean_enterprise.css` (ej: `/* === Dashboard styles === */`). Templates puramente decorativos pueden mantener `<style>` inline si son únicos a esa página y <20 líneas.

---

## 6. Convenciones para nuevos templates

Para evitar agregar más deuda visual, todo nuevo template debe:

✅ Extender `base.html` (autenticado) o `base_auth.html` (público)
✅ Usar SOLO las variables CSS documentadas en `DESIGN_SYSTEM.md`
✅ Usar `clean_enterprise.css` para estilos compartidos, no `<style>` inline
✅ Usar Bootstrap Icons (`bi-*`) — no introducir Font Awesome
✅ Si necesita gráficos: usar Chart.js + `CONTAFY_CHART_DEFAULTS`
✅ Si necesita confirmaciones: usar Swal con `customClass` estándar
✅ Cumplir checklist de "Anti-patterns" (sección 25 de DESIGN_SYSTEM.md)

❌ NO copiar gradientes/colores de templates antiguos (están desactualizados)
❌ NO crear nuevas clases CSS que dupliquen las existentes (`form-page-card`, `kpi-card`, etc.)

---

## 7. Métricas de éxito (post-refactor)

Una vez aplicada la migración completa, el sistema debe cumplir:

- [ ] 0 templates con gradientes púrpura/magenta `#667eea → #764ba2`
- [ ] 0 templates con `font-family: Arial` inline
- [ ] 0 templates que mezclen Font Awesome + Bootstrap Icons en el mismo archivo
- [ ] 100% de gráficos usando `CONTAFY_CHART_COLORS` y `CONTAFY_CHART_DEFAULTS`
- [ ] 100% de tablas listadas con clase `.contafy-table`
- [ ] 100% de modales informativos con header gradiente brand
- [ ] 100% de Swal con `customClass` y `buttonsStyling: false`
- [ ] <10 templates con `<style>` blocks >20 líneas (resto centralizado)
- [ ] 1 sola librería de iconos por template

---

**Mantenido por:** equipo Contafy
**Última actualización:** 2026-05-21
**Referencia:** [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md)
