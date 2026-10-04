# Sistema de Diseño Contafy

> **Versión:** 1.0 — 2026-05-21
> **Fuente de verdad:** `empresa/templates/empresa/landing.html` + `empresa/static/empresa/css/clean_enterprise.css`
> **Audiencia:** Equipo de desarrollo y diseño que mantiene templates HTML del sistema.

Este documento define el lenguaje visual oficial de Contafy. Todo nuevo template debe seguir estas reglas. Templates existentes deben migrar incrementalmente según el roadmap de `AUDIT_INCONSISTENCIAS.md`.

---

## Tabla de contenidos

1. [Identidad de Marca](#1-identidad-de-marca)
2. [Paleta de Colores](#2-paleta-de-colores)
3. [Gradientes Oficiales](#3-gradientes-oficiales)
4. [Tipografía](#4-tipografía)
5. [Tokens UI](#5-tokens-ui)
6. [Botones, Badges e Inputs base](#6-botones-badges-e-inputs-base)
7. [Sistema de Tarjetas](#7-sistema-de-tarjetas-cards)
8. [Sistema de Gráficos](#8-sistema-de-gráficos-charts)
9. [Sistema de Tablas](#9-sistema-de-tablas)
10. [Sistema de Modales](#10-sistema-de-modales)
11. [Alertas y Notificaciones](#11-alertas-y-notificaciones)
12. [Formularios e Inputs](#12-formularios-e-inputs)
13. [Sidebar autenticado](#13-sidebar-autenticado)
14. [Topbar autenticado](#14-topbar-autenticado)
15. [Dropdowns](#15-dropdowns)
16. [Empty States](#16-empty-states)
17. [Loaders y Spinners](#17-loaders-y-spinners)
18. [Paginación](#18-paginación)
19. [Breadcrumbs](#19-breadcrumbs)
20. [Tooltips y Popovers](#20-tooltips-y-popovers)
21. [Print / PDF styles](#21-print--pdf-styles)
22. [Iconografía](#22-iconografía)
23. [Patrones de animación](#23-patrones-de-animación)
24. [Responsive breakpoints](#24-responsive-breakpoints)
25. [Anti-patterns](#25-anti-patterns)

---

## 1. Identidad de Marca

**Logo:** `empresa/static/empresa/img/contafy-logo.png` — "C" estilizada con gradiente verde→azul + flecha característica.

**Wordmark:** `CONTAFY` en Montserrat Black (900), uppercase, letter-spacing `-0.5px`. La parte "FY" se renderiza siempre con `--grad-text` (verde-claro→azul-claro).

```html
<a href="..." class="brand">
  <img src="{% static 'empresa/img/contafy-logo.png' %}" alt="Contafy" class="logo-mark">
  CONTA<span>FY</span>
</a>
```

**Voz visual:** profesional, moderno, fintech-friendly. Sin elementos infantiles ni colores chillones.

**Conceptos clave:** confianza (azul), crecimiento (verde), claridad (espaciado generoso), velocidad (animaciones discretas pero presentes).

---

## 2. Paleta de Colores

### 2.1 Colores brand (los pilares)

| Token | Valor hex | Uso |
|---|---|---|
| `--c-green` | `#10b981` | Color brand primario — éxito, ingresos, CTA primario |
| `--c-green-d` | `#059669` | Verde oscuro — hover/active de elementos verdes |
| `--c-teal` | `#14b8a6` | Transición entre verde y azul, acentos secundarios |
| `--c-blue` | `#3b82f6` | Azul brand — información, neutros, links |
| `--c-blue-d` | `#2563eb` | Azul oscuro — hover/active de elementos azules |
| `--c-navy` | `#0f172a` | Sidebar, footer, fondos oscuros profundos |
| `--c-navy-2` | `#1e293b` | Variación más clara del navy |

### 2.2 Slates (grises neutros)

| Token | Valor hex | Uso |
|---|---|---|
| `--c-slate-1` | `#f8fafc` | Fondo de sección suave, hover de items, header de tablas |
| `--c-slate-2` | `#e2e8f0` | Borders sutiles, divisores, grids de gráficos |
| `--c-slate-3` | `#94a3b8` | Texto deshabilitado, placeholders |

### 2.3 Texto

| Token | Valor hex | Uso |
|---|---|---|
| `--c-text` | `#0f172a` | Texto principal (igual a navy) |
| `--c-muted` | `#64748b` | Subtítulos, captions, ejes de gráficos |

### 2.4 Semánticos

| Token | Valor hex | Uso |
|---|---|---|
| `--success-color` | `#10b981` | Mismo que `--c-green` |
| `--warning-color` | `#f59e0b` | Alertas ámbar, advertencias |
| `--danger-color` | `#ef4444` | Errores, eliminar, gastos |
| `--info-color` | `#0dcaf0` | Información secundaria (poco uso, preferir azul brand) |

### 2.5 CSS variables (`:root`)

Estas variables ya están definidas en `landing.html`. Migración pendiente: replicarlas en `clean_enterprise.css` para que TODO el sistema las herede (ver `AUDIT_INCONSISTENCIAS.md`).

```css
:root {
  --c-green:     #10b981;
  --c-green-d:   #059669;
  --c-teal:      #14b8a6;
  --c-blue:      #3b82f6;
  --c-blue-d:    #2563eb;
  --c-navy:      #0f172a;
  --c-navy-2:    #1e293b;
  --c-slate-1:   #f8fafc;
  --c-slate-2:   #e2e8f0;
  --c-slate-3:   #94a3b8;
  --c-text:      #0f172a;
  --c-muted:     #64748b;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --danger-color:  #ef4444;
}
```

---

## 3. Gradientes Oficiales

Solo **4 gradientes permitidos**. Cualquier otro gradiente es deuda visual.

### 3.1 `--grad-brand` — el principal

```css
--grad-brand: linear-gradient(135deg, #10b981 0%, #14b8a6 35%, #3b82f6 100%);
```

**Uso:**
- Botones primarios (`.btn-primary-hero`, `.btn-nav-cta`)
- Headers de modales informativos
- Headers de cards destacados
- Logo mark (cuadrado contenedor)
- Hover de items activos
- Item activo en paginación

### 3.2 `--grad-brand-r` — el reverso (hover)

```css
--grad-brand-r: linear-gradient(135deg, #3b82f6 0%, #14b8a6 65%, #10b981 100%);
```

**Uso:** Estado hover de elementos que usan `--grad-brand` — crea efecto de "respiro" sin perder identidad.

### 3.3 `--grad-text` — texto con relleno gradiente

```css
--grad-text: linear-gradient(135deg, #34d399 0%, #60a5fa 100%);
```

**Uso:** Aplicar a texto con técnica `-webkit-background-clip: text`. Específicamente:
- "FY" del wordmark CONTAFY
- Palabras destacadas en H1/H2 (ejemplo: "simple y poderosa", "ahora mismo")
- Números KPI grandes en planes pricing

```css
.grad-text {
  background: var(--grad-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### 3.4 `--grad-hero-bg` — fondo aurora oscuro

```css
--grad-hero-bg: linear-gradient(135deg, #0a1628 0%, #0f3a3a 35%, #0c2540 70%, #0a1628 100%);
```

**Uso:**
- Fondo del hero de la landing
- Fondo de secciones inmersivas (sección de demos, CTA finales)
- Headers de página oscuros (no usar en dashboards estándar)

Acompañar siempre con efecto aurora superpuesto:
```css
::before {
  background:
    radial-gradient(ellipse 70% 50% at 80% 30%, rgba(16,185,129,.18) 0%, transparent 65%),
    radial-gradient(ellipse 60% 45% at 25% 75%, rgba(59,130,246,.22) 0%, transparent 65%);
}
```

---

## 4. Tipografía

### 4.1 Fuentes oficiales

| Fuente | Pesos | Uso |
|---|---|---|
| **Montserrat** | 900 (Black) | Logo brand wordmark exclusivamente |
| **Space Grotesk** | 400, 500, 600, 700 | Display: H1, H2, H3, números KPI grandes |
| **Inter** | 400, 500, 600, 700, 800, 900 | Body, botones, labels, párrafos, tablas |
| **SF Mono / Menlo** | regular | Código, URLs, datos técnicos |

### 4.2 Importación HTML

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800;900&family=Montserrat:wght@700;800;900&display=swap" rel="stylesheet">
```

### 4.3 Variables CSS

```css
:root {
  --font-display: 'Space Grotesk', 'Inter', system-ui, sans-serif;
  --font-body:    'Inter', system-ui, sans-serif;
}
```

### 4.4 Jerarquía tipográfica

| Rol | Fuente | Tamaño | Peso | Letter-spacing | Uso |
|---|---|---|---|---|---|
| Hero H1 | Space Grotesk | `clamp(2.4rem, 5.5vw, 4.2rem)` | 700 | `-0.035em` | Landing hero |
| Section H2 | Space Grotesk | `clamp(2rem, 3.5vw, 2.75rem)` | 700 | `-0.03em` | Secciones de landing y headers de página |
| H3 / Card title large | Space Grotesk | `1.5rem` | 700 | `-0.02em` | Modal title, card heading principal |
| H4 / Sub heading | Space Grotesk | `1.25rem` | 700 | `-0.02em` | Sub-secciones |
| H5 | Inter | `1.1rem` | 700 | normal | Section group title |
| H6 / Card title | Inter | `1rem` | 700 | normal | Feature card title, sidebar group |
| Body / paragraph | Inter | `0.95-1rem` | 400 | normal | Texto general |
| Small | Inter | `0.875rem` | 400-500 | normal | Captions, helper text |
| Tiny / micro | Inter | `0.72-0.78rem` | 600-700 | `0.5-1px` | Badges, tags uppercase |
| Button label | Inter | `0.85-1rem` | 600-700 | normal | Todos los botones |
| Brand wordmark | Montserrat | `1.5-1.6rem` | 900 | `-0.5px` (uppercase) | Logo CONTAFY |
| Display number | Space Grotesk | `1.9-3.25rem` | 700 | `-0.02 a -0.04em` | KPI values, precios |
| Code / mono | SF Mono, Menlo | `0.7-0.85rem` | 400 | normal | URLs, IDs |

### 4.5 Anti-patterns tipográficos

- ❌ Arial, Times, Helvetica genéricos
- ❌ `font-weight: bold` sin valor numérico (usar 700)
- ❌ Letter-spacing positivo grande (>1px) en texto normal — solo en uppercase pequeño
- ❌ Mezclar Inter y Space Grotesk en el mismo bloque (titulares Space Grotesk, body Inter)
- ❌ Usar Montserrat fuera del logo brand

---

## 5. Tokens UI

### 5.1 Border-radius

| Token | Valor | Uso |
|---|---|---|
| `--radius-sm` | `6px` | Dropdown items, paginación |
| `--radius-md` | `8px` | Botones, inputs, alertas |
| `--radius-lg` | `10-12px` | Cards básicas, tooltips |
| `--radius-xl` | `16px` | Feature cards, modales |
| `--radius-2xl` | `20-22px` | Premium cards (pricing, demos, biz) |
| `--radius-pill` | `50px` | Badges, tags, botones pill |
| `--radius-full` | `50%` | Avatares, dots |

### 5.2 Sombras

```css
:root {
  --shadow-sm:    0 1px 2px rgba(15,23,42,.05);
  --shadow-md:    0 4px 12px rgba(15,23,42,.08);
  --shadow-lg:    0 12px 40px rgba(15,23,42,.12);
  --shadow-xl:    0 24px 60px rgba(15,23,42,.18);
  --shadow-brand: 0 12px 40px rgba(16,185,129,.25);
  --shadow-blue:  0 12px 40px rgba(59,130,246,.30);
}
```

**Cuándo usar:**
- `--shadow-sm`: cards en reposo, navbar, inputs focused
- `--shadow-md`: cards con elevación leve, dropdowns
- `--shadow-lg`: cards en hover, modales
- `--shadow-xl`: modales destacados, hero mockups
- `--shadow-brand`: botones primarios, elementos activos verdes
- `--shadow-blue`: elementos azules destacados (menos común)

### 5.3 Spacing system

| Token | Valor | Uso |
|---|---|---|
| `--space-1` | `0.25rem` | Gap entre dots, items micro |
| `--space-2` | `0.5rem` | Padding pills, gap inputs |
| `--space-3` | `0.75rem` | Gap entre cards pequeñas, padding celdas |
| `--space-4` | `1rem` | Padding base botones, gap general |
| `--space-5` | `1.25rem` | Padding cards básicas |
| `--space-6` | `1.5rem` | Gap secciones, padding modales |
| `--space-8` | `2rem` | Padding cards premium, gap grandes |
| `--space-10` | `2.5rem` | Padding hero CTAs |
| `--space-section` | `6.5rem 0` | Padding vertical de cada sección de landing |

### 5.4 Blur (glassmorphism)

| Uso | Valor |
|---|---|
| Navbar fija (top) | `blur(20px) saturate(180%)` |
| Modal backdrop | `blur(4px)` |
| Badges en imágenes | `blur(8-10px)` |
| Hero mockup wrapper | `blur(14px)` |

---

## 6. Botones, Badges e Inputs base

### 6.1 Botones — variantes oficiales

#### Primario hero (CTA principal)
```html
<a href="..." class="btn-primary-hero">
  <i class="bi bi-play-circle-fill"></i>
  <span>Probar demo gratis</span>
</a>
```
- Background: `var(--grad-brand)`
- Hover: `transform: translateY(-2px)` + `--shadow-brand`
- Padding: `.95rem 2.2rem`
- Border-radius: `12px`
- Font: Inter 700, 1rem

#### Ghost / outline hero (CTA secundario)
```html
<a href="..." class="btn-ghost-hero">
  Ver planes <i class="bi bi-arrow-right"></i>
</a>
```
- Background: `rgba(255,255,255,.05)` con `backdrop-filter: blur(10px)`
- Border: `1px solid rgba(255,255,255,.15)`
- Solo sobre fondos oscuros (hero, demos)

#### Botón estándar (formularios)
```html
<button class="btn btn-primary">Guardar</button>       <!-- acciones primarias -->
<button class="btn btn-outline-secondary">Cancelar</button>  <!-- acción secundaria -->
<button class="btn btn-danger">Eliminar</button>             <!-- acción destructiva -->
<button class="btn btn-success">Confirmar</button>           <!-- confirmación -->
```

Override de Bootstrap: `border-radius: 8px`, `font-weight: 600`, `padding: .5rem 1.1rem`.

#### Botón pequeño (tablas)
```html
<a href="..." class="btn btn-sm btn-outline-primary"><i class="bi bi-pencil"></i></a>
<a href="..." class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></a>
```
- Solo ícono en acciones de tabla
- `btn-sm` para `.btn-outline-*`

#### Mapeo semántico (qué color para qué acción)

| Acción | Color | Clase |
|---|---|---|
| Guardar / Crear / Continuar | Primario (verde brand) | `btn-primary` |
| Eliminar / Borrar / Cancelar definitivo | Rojo | `btn-danger` |
| Volver / Cancelar | Gris outline | `btn-outline-secondary` |
| Confirmar éxito | Verde | `btn-success` |
| Advertencia / cuidado | Ámbar | `btn-warning` |
| Información | Azul | `btn-info` |

### 6.2 Badges / Tags

#### Section tag (etiquetas pequeñas de sección)
```html
<span class="section-tag"><i class="bi bi-stars"></i> Funcionalidades</span>
```
- Background: `linear-gradient(135deg, rgba(16,185,129,.1), rgba(59,130,246,.1))`
- Border: `1px solid rgba(16,185,129,.2)`
- Padding: `.35rem 1rem`, border-radius pill, uppercase, letter-spacing `1.2px`

#### Hero badge (con dot pulsante)
```html
<div class="hero-badge">
  <span class="dot"></span>
  Contabilidad inteligente para PYMEs
</div>
```

#### Demo tag (glassmorphism sobre imagen)
```html
<span class="demo-tag blue">Comercial</span>
```
- Variantes: `blue`, `amber`, `green`, `brand`, `warm`, `cool`
- Backdrop-filter: `blur(8px)`

#### Estado / status pill
```html
<span class="badge bg-success">Activo</span>
<span class="badge bg-warning text-dark">Pendiente</span>
<span class="badge bg-danger">Vencido</span>
```
- Border-radius pill (`50px`)
- Solo colores semánticos (success/warning/danger), no púrpura ni cyan random

### 6.3 Inputs base (resumen — detalle completo en sección 12)

```html
<label class="form-label fw-600">
  Nombre <span class="text-danger">*</span>
</label>
<input type="text" class="form-control" placeholder="Ingresa...">
```

- `border-radius: 8px`, `border: 1.5px solid var(--c-slate-2)`
- Focus: border verde + glow suave
- Tipografía Inter 400, `font-size: .9rem`

---

## 7. Sistema de Tarjetas (Cards)

### 7.1 Tipos de tarjetas por propósito

| Variante | Clase | Uso | Tamaño | Border-radius | Padding |
|---|---|---|---|---|---|
| KPI / Métrica | `.kpi-card` | Dashboards, resumen — mostrar números importantes | `h-100`, min-h `120px` | `12px` | `1.25rem` |
| Feature / Funcionalidad | `.feat-card` | Listar características en grilla 3 col | auto | `16px` | `1.75rem 1.5rem` |
| Form container | `.form-page-card` | Wrapper de formularios | full | `12px` | `1.5rem` |
| Pricing | `.price-card` (`.featured`) | Planes y suscripciones | `h-100` | `22px` | `2.5rem 2.25rem` |
| Business cinemática | `.biz-card` | Tipos de negocio con imagen | `520px` | `22px` | `2.25rem 2rem` (overlay) |
| Demo entry | `.demo-card` | Acceso a demos | `440px` | `20px` | `1.75rem` (overlay) |
| Standard básica | `.card` (Bootstrap) | Listados y contenido genérico | auto | `12px` | `1.25rem` |

### 7.2 Anatomía estándar

```
┌─────────────────────────────┐
│ [Icon container]            │ ← ico-wrapper: 46-52px, border-radius 12-14px
│                             │
│ Título (700, 1rem)          │ ← font-display, color --c-text
│ Descripción (.875rem)       │ ← color --c-muted, line-height 1.6
│                             │
│ [CTA / Action]              │ ← opcional, btn al final
└─────────────────────────────┘
```

### 7.3 Ejemplo: KPI Card

```html
<div class="card kpi-card h-100 primary">
  <div class="card-body d-flex align-items-center">
    <div class="kpi-icon-wrapper me-3">
      <i class="bi bi-graph-up-arrow fs-4"></i>
    </div>
    <div>
      <div class="kpi-label">Ventas del mes</div>
      <div class="kpi-value">$4,820</div>
      <span class="badge mt-1">↑ 12% vs mes anterior</span>
    </div>
  </div>
</div>
```

Variantes de color: `.primary` (azul), `.success` (verde), `.warning` (ámbar), `.danger` (rojo).

### 7.4 Ejemplo: Feature Card

```html
<div class="feat-card">
  <div class="feat-ico green"><i class="bi bi-box-seam"></i></div>
  <h6>Inventario y Productos</h6>
  <p>Control de stock en tiempo real con escáner IA.</p>
</div>
```

### 7.5 Estados comunes

| Estado | Estilo |
|---|---|
| **Default** | `border: 1px solid var(--c-slate-2)`, fondo blanco, `--shadow-sm` |
| **Hover** | `transform: translateY(-6px)` + `--shadow-lg` + border `transparent` |
| **Featured** | Border gradiente con técnica `background: linear-gradient padding-box, var(--grad-brand) border-box` |
| **Loading** | `opacity: 0.6`, cursor `not-allowed` |
| **Selected** | Outline `2px var(--c-green)` |

### 7.6 Reglas obligatorias

- ❌ NO usar `box-shadow` inline arbitrario — siempre `--shadow-*`
- ❌ NO usar `.bg-primary`, `.text-success` Bootstrap como fondo de card
- ✅ Todas las cards de un dashboard mantienen mismo `border-radius` (no mezclar 12px con 16px en la misma vista)
- ✅ Iconos dentro de cards usan `kpi-icon-wrapper` o `.feat-ico`
- ✅ Acción primaria al final de la card, alineada a la derecha o full-width

---

## 8. Sistema de Gráficos (Charts)

### 8.1 Librería oficial

**Chart.js** vía CDN: `https://cdn.jsdelivr.net/npm/chart.js`

**Plugins permitidos:**
- `chartjs-adapter-date-fns` — fechas en ejes temporales
- `chartjs-plugin-datalabels@2` — labels sobre barras/segmentos

❌ **No introducir** otras librerías (ApexCharts, Plotly, Highcharts, D3 directo).

### 8.2 Paleta dedicada para gráficos

La paleta de gráficos puede diferir levemente del brand para asegurar contraste y distinción entre datasets:

```js
const CONTAFY_CHART_COLORS = {
  // Serie principal de 8 colores (para datasets múltiples)
  palette: [
    '#10b981',  // 1. Verde brand
    '#3b82f6',  // 2. Azul brand
    '#f59e0b',  // 3. Ámbar
    '#ef4444',  // 4. Rojo
    '#8b5cf6',  // 5. Púrpura
    '#14b8a6',  // 6. Teal
    '#f97316',  // 7. Naranja
    '#06b6d4',  // 8. Cyan
  ],
  // Semánticos FIJOS (no intercambiables)
  income:  '#10b981',  // ingresos siempre verde
  expense: '#ef4444',  // gastos siempre rojo
  profit:  '#3b82f6',  // utilidad siempre azul
  warning: '#f59e0b',  // alertas siempre ámbar
  // Transparencias
  fillAlpha:   0.15,
  borderAlpha: 1,
  // Ejes y grids
  grid:      '#e2e8f0',
  axisText:  '#64748b',
  tooltipBg: 'rgba(15, 23, 42, 0.95)',
};
```

### 8.3 Configuración visual estandarizada

```js
const CONTAFY_CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        font: { family: 'Inter', size: 12, weight: '500' },
        color: '#64748b',
        padding: 16,
        usePointStyle: true,
        pointStyle: 'circle',
      },
    },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      titleColor: '#fff',
      bodyColor: 'rgba(255,255,255,.85)',
      borderColor: 'rgba(16,185,129,.5)',
      borderWidth: 1,
      titleFont: { family: 'Inter', size: 13, weight: '700' },
      bodyFont:  { family: 'Inter', size: 12 },
      padding: 12,
      cornerRadius: 8,
      displayColors: true,
      boxPadding: 4,
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { font: { family: 'Inter', size: 11 }, color: '#64748b' },
    },
    y: {
      grid: { color: '#e2e8f0', drawBorder: false },
      ticks: { font: { family: 'Inter', size: 11 }, color: '#64748b' },
    },
  },
};
```

### 8.4 Tipos de gráfico — cuándo usar cada uno

| Tipo | Uso recomendado | Ejemplo en sistema |
|---|---|---|
| `bar` (vertical) | Comparación de categorías ≤8 | Ventas vs Gastos por mes |
| `bar` (horizontal) | Comparación con labels largos | Top productos vendidos |
| `line` | Tendencias temporales | Flujo de caja, ventas históricas |
| `area` (line con fill) | Volumen acumulado en el tiempo | Inventario evolutivo |
| `doughnut` | Composición de un total (3-7 partes) | Distribución de gastos |
| `pie` | Solo si no hay alternativa doughnut | (evitar — preferir doughnut) |
| `radar` | Comparación multi-dimensión (3-7 ejes) | Comparación sectorial |
| `mixed` (bar+line) | Dos métricas correlacionadas | Ingresos (barras) + margen (línea) |

### 8.5 Container estándar

```html
<div class="card">
  <div class="card-body">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h6 class="fw-bold mb-0">Ingresos vs Gastos</h6>
      <small class="text-muted">Últimos 6 meses</small>
    </div>
    <div style="position: relative; height: 320px;">
      <canvas id="miChart"></canvas>
    </div>
  </div>
</div>
```

**Altura del canvas wrapper:** fija en 240px / 320px / 400px según importancia. NO usar `aspect-ratio` libre.

### 8.6 Reglas obligatorias

- ✅ Fuente Inter en TODOS los textos (labels, ejes, tooltip)
- ✅ Tooltips siempre con fondo navy `rgba(15, 23, 42, 0.95)`, texto blanco, border verde sutil
- ✅ Grid solo en eje Y, color `#e2e8f0`, sin border vertical
- ✅ Bordes barras/líneas: 2px, color con `alpha: 1`
- ✅ Fills de áreas: mismo color del border con `alpha: 0.15`
- ✅ Border-radius en barras: 4px (modernidad)
- ✅ Si hay múltiples datasets, usar colores de `CONTAFY_CHART_COLORS.palette` en orden
- ✅ Variables semánticas (income/expense/profit/warning) son **inmutables**

### 8.7 Anti-patterns en gráficos

- ❌ Colores Material Design (`rgba(76, 175, 80)` verde, `rgba(244, 67, 54)` rojo)
- ❌ Tooltips con estilo default de Chart.js (gris genérico)
- ❌ Fonts diferentes a Inter
- ❌ Pie charts con >7 segmentos → usar bar horizontal
- ❌ Grid en eje X (solo eje Y)
- ❌ Leyendas con cuadrados grandes → siempre `pointStyle: 'circle'` + `usePointStyle: true`

### 8.8 Helper recomendado

Crear (futuro) `empresa/static/js/contafy_charts.js`:

```js
// contafy_charts.js
window.CONTAFY_CHART_COLORS   = { /* ver 8.2 */ };
window.CONTAFY_CHART_DEFAULTS = { /* ver 8.3 */ };
```

Importar en `base.html`:
```html
<script src="{% static 'js/contafy_charts.js' %}"></script>
```

Y usar en cualquier template con gráficos:
```js
new Chart(ctx, {
  type: 'bar',
  data: { /* ... */ },
  options: { ...CONTAFY_CHART_DEFAULTS, /* overrides específicos */ },
});
```

---

## 9. Sistema de Tablas

### 9.1 Anatomía estándar

```html
<div class="table-responsive">
  <table class="table contafy-table table-hover align-middle">
    <thead>
      <tr>
        <th>Columna 1</th>
        <th class="text-end">Monto</th>
        <th class="text-center">Acciones</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Producto X</td>
        <td class="text-end fw-600">$1,234.00</td>
        <td class="text-center">
          <a href="..." class="btn btn-sm btn-outline-primary"><i class="bi bi-pencil"></i></a>
          <a href="..." class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></a>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### 9.2 Estilo unificado (a centralizar en `clean_enterprise.css`)

```css
.contafy-table thead th {
  background: var(--c-slate-1);
  color: var(--c-text);
  font-weight: 700;
  font-size: .85rem;
  text-transform: uppercase;
  letter-spacing: .5px;
  border-bottom: 2px solid var(--c-slate-2);
  padding: .75rem 1rem;
}
.contafy-table tbody td {
  padding: .75rem 1rem;
  border-top: 1px solid var(--c-slate-2);
  font-size: .9rem;
}
.contafy-table tbody tr {
  transition: background .15s ease;
}
.contafy-table tbody tr:hover {
  background: rgba(16, 185, 129, .04);
}
.contafy-table .text-end,
.contafy-table .text-right {
  font-variant-numeric: tabular-nums;
}
```

### 9.3 Reglas

- ✅ Siempre dentro de `.table-responsive` para scroll horizontal en mobile
- ✅ `align-middle` para verticalmente centrar
- ✅ Columnas numéricas con `text-end` y `font-variant-numeric: tabular-nums`
- ❌ NO usar `table-bordered` (demasiado ruido)
- ❌ NO mezclar `table-striped` y `table-hover` (elegir uno)
- ✅ Datatables (con JS) solo en listados con >50 filas potenciales

### 9.4 Empty state en tabla

Cuando la tabla está vacía, NO mostrar `<tbody>` vacío. Usar el componente empty-state (sección 16) reemplazando la tabla:

```html
{% if items %}
  <table class="table contafy-table">...</table>
{% else %}
  {% include "empresa/_components/empty_state.html" with title="Sin registros" %}
{% endif %}
```

---

## 10. Sistema de Modales

### 10.1 Anatomía estándar

```html
<div class="modal fade" id="miModal" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered modal-lg">
    <div class="modal-content">
      <div class="modal-header" style="background: var(--grad-brand); color: #fff;">
        <h5 class="modal-title fw-700">
          <i class="bi bi-info-circle me-2"></i> Título del modal
        </h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body p-4">
        <!-- contenido -->
      </div>
      <div class="modal-footer bg-light">
        <button class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancelar</button>
        <button class="btn btn-primary">Confirmar</button>
      </div>
    </div>
  </div>
</div>
```

### 10.2 Variantes por intención

| Tipo | Header background | Ícono recomendado |
|---|---|---|
| Info / Formulario | `var(--grad-brand)` | `bi-info-circle`, `bi-pencil-square` |
| Peligro / Eliminar | `var(--danger-color)` sólido | `bi-exclamation-triangle-fill` |
| Éxito / Confirmación | `var(--success-color)` sólido | `bi-check-circle-fill` |
| Advertencia | `var(--warning-color)` sólido | `bi-exclamation-circle` |

### 10.3 Tamaños

| Clase | Uso |
|---|---|
| `modal-sm` | Confirmaciones rápidas |
| (default) | Forms cortos, info |
| `modal-lg` | Forms largos (recomendado por defecto) |
| `modal-xl` | Visualizaciones, dashboards mini, listas grandes |

### 10.4 Reglas

- ✅ Siempre `modal-dialog-centered` (verticalmente centrado)
- ✅ Override CSS: `.modal-content { border-radius: 16px; box-shadow: var(--shadow-xl); }`
- ✅ `btn-close-white` cuando header es oscuro
- ✅ Footer con `bg-light` para separación visual
- ❌ NO modal headers sin color de marca (gris Bootstrap se ve plano)
- ❌ NO `data-bs-backdrop="static"` sin razón (UX hostil)

---

## 11. Alertas y Notificaciones

### 11.1 SweetAlert2 (Swal) — configuración estándar

```js
Swal.fire({
  title: '¿Eliminar producto?',
  text: 'Esta acción no se puede deshacer',
  icon: 'warning',
  showCancelButton: true,
  confirmButtonText: 'Sí, eliminar',
  cancelButtonText: 'Cancelar',
  confirmButtonColor: '#ef4444',  // --danger-color
  cancelButtonColor: '#94a3b8',   // --c-slate-3
  customClass: {
    popup: 'contafy-swal',
    confirmButton: 'btn btn-danger',
    cancelButton:  'btn btn-outline-secondary'
  },
  buttonsStyling: false,
});
```

### 11.2 Mapeo de colores por tipo Swal

| Tipo Swal | Ícono | Color botón confirmar | Uso |
|---|---|---|---|
| `success` | check verde | `#10b981` | Confirmación exitosa |
| `error` | x rojo | `#ef4444` | Errores |
| `warning` | ! ámbar | `#f59e0b` | Confirmar eliminación |
| `info` | i azul | `#3b82f6` | Información |
| `question` | ? azul | `#3b82f6` | Decisiones |

### 11.3 Alertas Bootstrap inline

```html
<div class="alert alert-success" role="alert">
  <i class="bi bi-check-circle-fill me-2"></i>
  Guardado correctamente
</div>

<div class="alert alert-danger" role="alert">
  <i class="bi bi-exclamation-triangle-fill me-2"></i>
  Error al procesar la solicitud
</div>

<div class="alert alert-warning" role="alert">
  <i class="bi bi-exclamation-circle-fill me-2"></i>
  Stock bajo en 3 productos
</div>

<div class="alert alert-info" role="alert">
  <i class="bi bi-info-circle-fill me-2"></i>
  Recuerda configurar tus impuestos
</div>
```

**Estilo unificado (a aplicar en `clean_enterprise.css`):**
```css
.alert {
  border-radius: 8px;
  padding: .85rem 1rem;
  border-left: 4px solid;
  border-top: 0; border-right: 0; border-bottom: 0;
}
.alert-success { background: rgba(16,185,129,.08); color: #065f46; border-left-color: #10b981; }
.alert-danger  { background: rgba(239,68,68,.08); color: #7f1d1d; border-left-color: #ef4444; }
.alert-warning { background: rgba(245,158,11,.08); color: #78350f; border-left-color: #f59e0b; }
.alert-info    { background: rgba(59,130,246,.08); color: #1e3a8a; border-left-color: #3b82f6; }
```

### 11.4 Toasts (notificaciones no bloqueantes)

```js
const Toast = Swal.mixin({
  toast: true,
  position: 'top-end',
  showConfirmButton: false,
  timer: 3500,
  timerProgressBar: true,
  didOpen: (toast) => {
    toast.addEventListener('mouseenter', Swal.stopTimer);
    toast.addEventListener('mouseleave', Swal.resumeTimer);
  }
});
Toast.fire({ icon: 'success', title: 'Guardado correctamente' });
```

---

## 12. Formularios e Inputs

### 12.1 Inputs base — override de Bootstrap

```css
.form-control,
.form-select {
  border-radius: 8px;
  border: 1.5px solid var(--c-slate-2);
  padding: .55rem .85rem;
  font-size: .9rem;
  font-family: var(--font-body);
  transition: border-color .15s, box-shadow .15s;
}
.form-control:focus,
.form-select:focus {
  border-color: var(--c-green);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, .15);
  outline: none;
}
.form-control:disabled,
.form-select:disabled {
  background: var(--c-slate-1);
  opacity: .65;
}
.form-control::placeholder {
  color: var(--c-slate-3);
}
```

### 12.2 Labels y marcadores requeridos

```html
<label for="id_nombre" class="form-label fw-600">
  Nombre <span class="text-danger">*</span>
</label>
<input type="text" id="id_nombre" name="nombre" class="form-control" required>
<small class="form-text text-muted">Texto de ayuda opcional</small>
```

**Convención:**
- Required: asterisco rojo `*` después del label
- Opcional: NO marcar (todo lo no-required se asume opcional)
- Helper text: `<small class="form-text text-muted">` debajo del input

### 12.3 Estados de validación

```html
<input type="email" class="form-control is-invalid" value="malformatted">
<div class="invalid-feedback">Email inválido</div>

<input type="text" class="form-control is-valid" value="OK">
<div class="valid-feedback">Disponible</div>
```

### 12.4 Inputs especiales

#### Date
```html
<div class="input-group">
  <span class="input-group-text"><i class="bi bi-calendar3"></i></span>
  <input type="date" class="form-control">
</div>
```

#### Money
```html
<div class="input-group">
  <span class="input-group-text">$</span>
  <input type="number" class="form-control text-end" step="0.01" min="0">
</div>
```

#### Select largo (>10 opciones)
Usar `tom-select` o `select2` con estilos override para que mantengan border-radius 8px y border verde en focus.

#### File upload
Ocultar el `<input type="file">` nativo y usar botón custom:
```html
<label class="btn btn-outline-primary">
  <i class="bi bi-cloud-upload me-1"></i> Seleccionar archivo
  <input type="file" hidden onchange="...">
</label>
<span class="ms-2 text-muted small filename-preview">Ningún archivo</span>
```

#### Switch
```html
<div class="form-check form-switch">
  <input class="form-check-input" type="checkbox" id="switchActivo" checked>
  <label class="form-check-label" for="switchActivo">Activo</label>
</div>
```
- Color activo: `var(--c-green)` (override de Bootstrap blue)

### 12.5 Layout estandarizado

- Grid: `.row > .col-md-6` para 2 columnas, `.col-md-4` para 3
- Espaciado vertical: `mb-3` entre campos
- Agrupar lógicamente con `<fieldset>` o sección con `<h5>` divisor
- Submit al final con `d-grid` (full-width) o `d-flex justify-content-end gap-2` (botones derecha)

---

## 13. Sidebar autenticado

### 13.1 Estructura visual (ya en `base.html`)

```css
.sidebar {
  width: var(--sidebar-width, 260px);
  background: var(--c-navy);
  color: rgba(255, 255, 255, .9);
  height: 100vh;
  position: fixed;
  left: 0; top: 0;
  transition: transform .3s ease;
  z-index: 1000;
}
.sidebar.collapsed,
@media (max-width: 768px) { .sidebar { transform: translateX(-100%); } }
.sidebar.show { transform: translateX(0); }
```

### 13.2 Items

```css
.sidebar .nav-link {
  color: rgba(255, 255, 255, .7);
  padding: .55rem 1rem;
  border-radius: 6px;
  margin: .15rem .5rem;
  transition: all .2s;
  font-size: .9rem;
}
.sidebar .nav-link:hover {
  background: rgba(255, 255, 255, .06);
  color: #fff;
}
.sidebar .nav-link.active {
  background: rgba(255, 255, 255, .08);
  color: #fff;
  border-left: 3px solid var(--c-green);
  padding-left: calc(1rem - 3px);
}
```

### 13.3 Grupos / secciones

```html
<div class="sidebar-section">
  <h6 class="sidebar-group-title">Operación</h6>
  <a href="..." class="nav-link"><i class="bi bi-cart3 me-2"></i> Ventas</a>
  <a href="..." class="nav-link"><i class="bi bi-box-seam me-2"></i> Inventario</a>
</div>
```

```css
.sidebar-group-title {
  color: rgba(255, 255, 255, .4);
  font-size: .7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .8px;
  padding: 1rem 1.25rem .5rem;
  margin: 0;
}
```

### 13.4 Iconografía sidebar

- **Solo Bootstrap Icons** (`bi-*`) — nunca Font Awesome
- Tamaño: `1rem`, alineado al inicio con `me-2`
- Iconos sugeridos: `bi-cart3` (ventas), `bi-box-seam` (inventario), `bi-receipt` (gastos), `bi-graph-up` (reportes), `bi-people` (clientes), `bi-gear` (configuración)

### 13.5 User/avatar al final

```html
<div class="sidebar-footer">
  <div class="dropdown">
    <button class="user-trigger" data-bs-toggle="dropdown">
      <div class="user-avatar">D</div>
      <span class="user-name">demo_comercio</span>
      <i class="bi bi-chevron-up"></i>
    </button>
    <ul class="dropdown-menu dropdown-menu-end">
      <li><a class="dropdown-item" href="..."><i class="bi bi-person me-2"></i> Mi perfil</a></li>
      <li><a class="dropdown-item" href="..."><i class="bi bi-building me-2"></i> Mi empresa</a></li>
      <li><hr class="dropdown-divider"></li>
      <li><a class="dropdown-item text-danger" href="..."><i class="bi bi-box-arrow-right me-2"></i> Cerrar sesión</a></li>
    </ul>
  </div>
</div>
```

---

## 14. Topbar autenticado

### 14.1 Estructura

```html
<nav class="topbar navbar navbar-light bg-white border-bottom px-4 py-2 sticky-top shadow-sm">
  <button class="btn btn-link p-0 me-3" id="sidebarToggle">
    <i class="bi bi-list fs-4"></i>
  </button>
  <!-- Buscador global -->
  <form class="search-global flex-grow-1 me-3">
    <div class="input-group" style="max-width: 400px;">
      <span class="input-group-text bg-light border-0"><i class="bi bi-search"></i></span>
      <input type="text" class="form-control bg-light border-0" placeholder="Buscar...">
    </div>
  </form>
  <!-- Notificaciones -->
  <div class="dropdown me-3">
    <button class="btn btn-link p-0 position-relative">
      <i class="bi bi-bell fs-5"></i>
      <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">3</span>
    </button>
  </div>
  <!-- Empresa actual -->
  <div class="empresa-actual me-3 d-none d-md-flex align-items-center">
    <i class="bi bi-building text-muted me-2"></i>
    <span class="fw-600">Minimarket Don Pepe</span>
  </div>
</nav>
```

### 14.2 Reglas

- Background: blanco
- Sombra: `var(--shadow-sm)`
- Sticky: `sticky-top`
- Logo brand a la izquierda (mismo logo que landing)
- Buscador global: input sin border, fondo `var(--c-slate-1)`, `border-radius: 8px`
- Notificaciones: bell con badge contador rojo
- Empresa actual: nombre + ícono `bi-building`

---

## 15. Dropdowns

### 15.1 Estilo unificado

```css
.dropdown-menu {
  border-radius: 10px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--c-slate-2);
  padding: .5rem;
  min-width: 200px;
}
.dropdown-item {
  border-radius: 6px;
  padding: .5rem .75rem;
  font-size: .88rem;
  transition: background .15s;
}
.dropdown-item:hover {
  background: var(--c-slate-1);
  color: var(--c-text);
}
.dropdown-item.text-danger:hover {
  background: rgba(239, 68, 68, .08);
}
.dropdown-divider {
  border-color: var(--c-slate-2);
  margin: .35rem 0;
}
```

### 15.2 Convenciones

- Items siempre con ícono al inicio (`me-2`)
- Item destructivo (eliminar, logout) con clase `text-danger`
- Separadores con `<hr class="dropdown-divider">`
- Header de grupo (opcional): `<h6 class="dropdown-header">`

---

## 16. Empty States

### 16.1 Patrón estándar

```html
<div class="empty-state text-center py-5">
  <i class="bi bi-inbox display-4 text-muted"></i>
  <h6 class="mt-3 fw-600 text-muted">No hay registros aún</h6>
  <p class="text-muted small mb-3">Crea tu primer registro para empezar a gestionar.</p>
  <a href="..." class="btn btn-primary">
    <i class="bi bi-plus-circle me-1"></i> Crear nuevo
  </a>
</div>
```

### 16.2 Iconos sugeridos por contexto

| Contexto | Ícono |
|---|---|
| Tabla / Listado vacío | `bi-inbox` |
| Búsqueda sin resultados | `bi-search` |
| Sin productos | `bi-box-seam` |
| Sin ventas | `bi-cart-x` |
| Sin notificaciones | `bi-bell-slash` |
| Sin datos para gráfico | `bi-graph-down` |
| Error | `bi-exclamation-triangle` |

### 16.3 Componente reutilizable (recomendado)

Crear `empresa/templates/empresa/_components/empty_state.html`:

```django
<div class="empty-state text-center py-5">
  <i class="bi {{ icon|default:'bi-inbox' }} display-4 text-muted"></i>
  <h6 class="mt-3 fw-600 text-muted">{{ title }}</h6>
  {% if description %}<p class="text-muted small mb-3">{{ description }}</p>{% endif %}
  {% if cta_url and cta_label %}
    <a href="{{ cta_url }}" class="btn btn-primary">
      <i class="bi bi-plus-circle me-1"></i> {{ cta_label }}
    </a>
  {% endif %}
</div>
```

Usar con:
```django
{% include "empresa/_components/empty_state.html" with title="Sin ventas" description="Registra tu primera venta" cta_url=crear_venta_url cta_label="Nueva venta" icon="bi-cart-x" %}
```

---

## 17. Loaders y Spinners

### 17.1 Spinner inline (en botón mientras procesa)

```html
<button class="btn btn-primary" disabled>
  <span class="spinner-border spinner-border-sm me-2"></span>
  Procesando...
</button>
```

### 17.2 Overlay de página completa

```html
<div class="page-loader" style="display:none;">
  <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;"></div>
  <div class="mt-3 text-muted">Cargando...</div>
</div>
```

```css
.page-loader {
  position: fixed; inset: 0;
  background: rgba(255, 255, 255, .85);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
```

### 17.3 Skeleton loaders (para listados)

```html
<p class="placeholder-glow">
  <span class="placeholder col-7"></span>
  <span class="placeholder col-4"></span>
  <span class="placeholder col-4"></span>
  <span class="placeholder col-6"></span>
  <span class="placeholder col-8"></span>
</p>
```

### 17.4 Color del spinner

Override Bootstrap:
```css
.spinner-border.text-primary { color: var(--c-green) !important; }
```

---

## 18. Paginación

### 18.1 Componente existente

`empresa/templates/empresa/components/pagination.html` ya existe — extender su uso a todos los listados.

### 18.2 Estilo

```css
.pagination .page-item .page-link {
  border-radius: 6px;
  margin: 0 .15rem;
  border: 1px solid var(--c-slate-2);
  color: var(--c-text);
  font-weight: 600;
  font-size: .88rem;
  padding: .4rem .75rem;
  transition: all .15s;
}
.pagination .page-item .page-link:hover {
  background: var(--c-slate-1);
  border-color: var(--c-slate-3);
}
.pagination .page-item.active .page-link {
  background: var(--grad-brand);
  border-color: transparent;
  color: #fff;
}
.pagination .page-item.disabled .page-link {
  opacity: .5;
  cursor: not-allowed;
}
```

### 18.3 Info text de paginación

```html
<div class="d-flex justify-content-between align-items-center mt-3">
  <small class="text-muted">Mostrando {{ page_obj.start_index }}-{{ page_obj.end_index }} de {{ page_obj.paginator.count }}</small>
  {% include "empresa/components/pagination.html" %}
</div>
```

---

## 19. Breadcrumbs

### 19.1 Patrón estándar

```html
<nav aria-label="breadcrumb">
  <ol class="breadcrumb">
    <li class="breadcrumb-item"><a href="...">Inicio</a></li>
    <li class="breadcrumb-item"><a href="...">Inventario</a></li>
    <li class="breadcrumb-item active" aria-current="page">Crear producto</li>
  </ol>
</nav>
```

### 19.2 Override CSS

```css
.breadcrumb {
  background: transparent;
  padding: .5rem 0;
  margin-bottom: 1rem;
  font-size: .88rem;
}
.breadcrumb-item + .breadcrumb-item::before {
  content: "›";  /* o usar SVG bi-chevron-right */
  color: var(--c-slate-3);
  font-weight: 600;
}
.breadcrumb-item a {
  color: var(--c-muted);
  text-decoration: none;
}
.breadcrumb-item a:hover {
  color: var(--c-green-d);
}
.breadcrumb-item.active {
  color: var(--c-text);
  font-weight: 600;
}
```

---

## 20. Tooltips y Popovers

### 20.1 Inicialización global

En `base.html`, al final:

```html
<script>
  // Inicializar tooltips de Bootstrap
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });
</script>
```

### 20.2 Uso en templates

```html
<button class="btn btn-sm btn-outline-secondary"
        data-bs-toggle="tooltip"
        data-bs-placement="top"
        title="Información adicional">
  <i class="bi bi-info-circle"></i>
</button>
```

### 20.3 Estilo (override)

```css
.tooltip-inner {
  background: var(--c-navy);
  color: #fff;
  border-radius: 6px;
  padding: .35rem .65rem;
  font-size: .8rem;
  font-family: var(--font-body);
  max-width: 220px;
}
.tooltip .tooltip-arrow::before {
  border-color: var(--c-navy);
}
```

---

## 21. Print / PDF styles

### 21.1 Reglas base (incluir en `clean_enterprise.css`)

```css
@media print {
  /* Ocultar elementos de navegación */
  .no-print,
  .sidebar,
  .topbar,
  .btn,
  .pagination,
  .dropdown,
  nav { display: none !important; }

  /* Tamaño de página */
  @page {
    margin: 1.5cm;
    size: A4;
  }

  /* Forzar negros para impresión */
  body, .card, .table {
    background: white !important;
    color: black !important;
    box-shadow: none !important;
  }

  /* Evitar quebrar tablas */
  table, tr, td, th {
    page-break-inside: avoid;
  }

  /* Mostrar URLs en links */
  a[href]:after {
    content: " (" attr(href) ")";
    font-size: .85em;
    color: #555;
  }

  /* Convertir gradientes a sólidos */
  .modal-header,
  [style*="gradient"] {
    background: var(--c-green) !important;
  }

  /* Print-only content */
  .print-only { display: block !important; }
}
```

### 21.2 Header/footer en impresión

```html
<div class="print-only" style="display:none;">
  <div class="print-header">
    <img src="..." alt="Logo Contafy" style="height: 40px;">
    <h3>Estado de Resultados — {{ empresa.nombre }}</h3>
    <p>Periodo: {{ fecha_inicio }} a {{ fecha_fin }}</p>
  </div>
</div>
```

### 21.3 Templates que ya usan @media print

- `balance_general.html`
- `estado_resultado.html`
- `reporte_ia.html`

Migrar todas estas reglas a `clean_enterprise.css` para que sean globales en lugar de duplicadas en cada template.

---

## 22. Iconografía

### 22.1 Regla maestra: una sola librería por template

| Librería | Uso recomendado |
|---|---|
| **Bootstrap Icons** (`bi-*`) | UI moderna: landing, dashboards, listados, navbar, sidebar, cards nuevas — todo lo nuevo |
| **Font Awesome** (`fa-*`) | Solo módulos legacy que ya lo usan (formularios complejos heredados como registro/login) |

**Regla:** Dentro de un mismo archivo template, usar UNA SOLA librería. NO mezclar `bi-*` y `fa-*` en el mismo HTML.

### 22.2 Tamaños estándar

| Tamaño | Uso |
|---|---|
| `0.7rem` | Iconos micro en badges |
| `0.85rem` | Iconos en text inline |
| `1rem` | Iconos en sidebar, nav-link, lista |
| `1.2rem` | Iconos en botones medianos |
| `1.4rem` | Iconos en feature cards |
| `1.8rem` | Iconos en hero, empty state grandes |
| `2.5rem` | Iconos decorativos en cards premium |

### 22.3 Colores

| Color | Cuándo |
|---|---|
| `currentColor` (heredado del padre) | Default — el ícono toma el color del texto |
| `var(--c-green)` | Acciones de éxito, ingresos |
| `var(--c-blue)` | Información, links |
| `var(--warning-color)` | Advertencias |
| `var(--danger-color)` | Eliminar, errores |
| `var(--c-muted)` | Iconos secundarios, captions |
| `rgba(255,255,255,.7)` | Iconos sobre fondos oscuros (sidebar, hero) |

### 22.4 Iconos canónicos por acción (Bootstrap Icons)

| Acción | Ícono |
|---|---|
| Crear / Nuevo | `bi-plus-circle` o `bi-plus-lg` |
| Editar | `bi-pencil` o `bi-pencil-square` |
| Eliminar | `bi-trash` o `bi-trash3` |
| Ver detalle | `bi-eye` |
| Buscar | `bi-search` |
| Filtrar | `bi-funnel` |
| Exportar | `bi-download` |
| Importar | `bi-upload` o `bi-cloud-upload` |
| Imprimir | `bi-printer` |
| Configurar | `bi-gear` o `bi-sliders` |
| Cerrar sesión | `bi-box-arrow-right` |
| Volver | `bi-arrow-left` |
| Avanzar | `bi-arrow-right` o `bi-chevron-right` |
| Éxito | `bi-check-circle-fill` |
| Error | `bi-x-circle-fill` |
| Advertencia | `bi-exclamation-triangle-fill` |
| Info | `bi-info-circle-fill` |

---

## 23. Patrones de animación

### 23.1 Transiciones estándar

| Patrón | Valores | Uso |
|---|---|---|
| Hover suave de cards | `transform: translateY(-6px); box-shadow: ...; transition: all .25-.35s;` | Cualquier card clickeable |
| Hover de botones | `transform: translateY(-2px); box-shadow: --shadow-brand;` 0.2s | Botones primarios |
| Image zoom en card | `transform: scale(1.07-1.08); transition: transform .7-.8s cubic-bezier(.4,0,.2,1);` | Imágenes en biz-card, demo-card |
| Carousel slide | `transform: translateX(...); transition: transform .5s cubic-bezier(.4,0,.2,1);` | Carrusel de funcionalidades |
| Fade in al cargar | `opacity 0 → 1`, 0.4s ease | Modal show, dropdown |
| Pulse dot | Keyframe 2s ease-in-out infinite, `opacity 1 ↔ 0.4` | Live indicator, badge "En vivo" |
| Aurora float | 18s ease-in-out infinite, transform leve | Hero background |
| Bar chart animation | `height 0 → final` 0.6s cubic-bezier(.4,0,.2,1), staggered 50ms | Animación inicial de gráficos |

### 23.2 Cubic-bezier oficial

`cubic-bezier(.4, 0, .2, 1)` — Material Design "ease-out emphasized". Usar para todas las transiciones suaves no triviales.

### 23.3 Reglas

- ❌ NO animaciones >1s (excepto loops sutiles como aurora)
- ❌ NO `transition: all` con muchas propiedades (especificar las necesarias)
- ✅ Siempre `transform` y `opacity` (no `top`, `left`, `width`)
- ✅ `will-change: transform` solo si la animación es continua

---

## 24. Responsive breakpoints

### 24.1 Breakpoints oficiales

| Nombre | Min-width | Uso |
|---|---|---|
| Mobile | `<480px` | Stacked, 1 col, sidebar oculto |
| Mobile L | `480px` | Pequeñas mejoras de espaciado |
| Tablet | `768px` | Grids 2 col, sidebar colapsable |
| Desktop | `992px` | Grids 3 col, sidebar visible |
| Desktop L | `1200px` | Layout máximo |
| Desktop XL | `1400px` | Para containers wide |

### 24.2 Media queries patrón

```css
/* Mobile-first: estilos base son mobile */
.componente { /* mobile */ }

@media (min-width: 768px) {
  .componente { /* tablet+ */ }
}

@media (min-width: 992px) {
  .componente { /* desktop+ */ }
}
```

### 24.3 Reglas

- ✅ Mobile-first (estilos base para mobile, media queries para escalar arriba)
- ✅ Sidebar SIEMPRE oculto en mobile (`transform: translateX(-100%)`)
- ✅ Grids: `grid-template-columns` adaptativo según breakpoint
- ✅ Tamaños tipográficos: usar `clamp(min, preferred, max)` para fluidez

---

## 25. Anti-patterns

### Resumen prohibido

❌ **Colores fuera del sistema:**
- Gradientes púrpura/magenta `#667eea → #764ba2`
- Verde-gris Bootstrap `#28a745 → #20c997`, `#27ae60 → #2c3e50`
- Turquesa random `#4ecdc4 → #45b7d1`
- Material Design verde/rojo (`rgba(76, 175, 80)`, `rgba(244, 67, 54)`)

❌ **Tipografía sin sistema:**
- Arial, Times, Helvetica genéricos
- `font-family` inline sin variables
- Pesos arbitrarios (`bold` en vez de `700`)
- Letter-spacing positivo grande (>1px) en texto normal

❌ **Estructural:**
- `<style>` blocks de >20 líneas en templates (mover a CSS global)
- `style="..."` inline para propiedades de marca (colores, gradientes, fonts)
- Mezclar `bi-*` (Bootstrap Icons) y `fa-*` (Font Awesome) en el mismo template
- `box-shadow` arbitrario en lugar de tokens `--shadow-*`

❌ **Componentes:**
- Cards con border/shadow custom inline en lugar de las variantes oficiales
- Modal headers sin color de marca (gris Bootstrap default)
- Tablas con `table-bordered` (demasiado ruido)
- Mezclar `table-striped` y `table-hover`
- Pie charts con >7 segmentos (usar bar horizontal)
- Tooltips con estilo default Bootstrap

❌ **Gráficos:**
- Mezclar Chart.js con ApexCharts/Plotly en el mismo template
- Colores hardcoded sin la paleta `CONTAFY_CHART_COLORS`
- Tooltips default de Chart.js
- Variables semánticas intercambiables (ingresos en rojo, gastos en verde)

❌ **JavaScript / Notificaciones:**
- `alert()` nativo (usar Swal o `.alert` Bootstrap)
- `confirmButtonColor: '#28a745'` en Swal (usar `#10b981`)
- Toasts con estilos personalizados sin la mixin estándar

❌ **UX:**
- Modales con `data-bs-backdrop="static"` sin razón
- Formularios sin marcador `*` en campos requeridos
- Tablas vacías sin empty-state
- Botones sin íconos descriptivos en acciones críticas

---

## Apéndice A — Variables CSS completas (para `clean_enterprise.css`)

```css
:root {
  /* Colores brand */
  --c-green:     #10b981;
  --c-green-d:   #059669;
  --c-teal:      #14b8a6;
  --c-blue:      #3b82f6;
  --c-blue-d:    #2563eb;
  --c-navy:      #0f172a;
  --c-navy-2:    #1e293b;

  /* Slates */
  --c-slate-1:   #f8fafc;
  --c-slate-2:   #e2e8f0;
  --c-slate-3:   #94a3b8;

  /* Texto */
  --c-text:      #0f172a;
  --c-muted:     #64748b;

  /* Semánticos */
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --danger-color:  #ef4444;
  --info-color:    #0dcaf0;

  /* Gradientes */
  --grad-brand:    linear-gradient(135deg, #10b981 0%, #14b8a6 35%, #3b82f6 100%);
  --grad-brand-r:  linear-gradient(135deg, #3b82f6 0%, #14b8a6 65%, #10b981 100%);
  --grad-text:     linear-gradient(135deg, #34d399 0%, #60a5fa 100%);
  --grad-hero-bg:  linear-gradient(135deg, #0a1628 0%, #0f3a3a 35%, #0c2540 70%, #0a1628 100%);

  /* Sombras */
  --shadow-sm:    0 1px 2px rgba(15,23,42,.05);
  --shadow-md:    0 4px 12px rgba(15,23,42,.08);
  --shadow-lg:    0 12px 40px rgba(15,23,42,.12);
  --shadow-xl:    0 24px 60px rgba(15,23,42,.18);
  --shadow-brand: 0 12px 40px rgba(16,185,129,.25);
  --shadow-blue:  0 12px 40px rgba(59,130,246,.30);

  /* Tipografía */
  --font-display: 'Space Grotesk', 'Inter', system-ui, sans-serif;
  --font-body:    'Inter', system-ui, sans-serif;

  /* Border-radius */
  --radius-sm:   6px;
  --radius-md:   8px;
  --radius-lg:   12px;
  --radius-xl:   16px;
  --radius-2xl:  22px;
  --radius-pill: 50px;
}
```

---

## Apéndice B — Recursos externos oficiales

| Recurso | URL |
|---|---|
| Bootstrap 5.3.3 | `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css` |
| Bootstrap Icons | `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css` |
| Font Awesome 6 (legacy) | `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css` |
| Google Fonts (Inter + Space Grotesk + Montserrat) | `https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800;900&family=Montserrat:wght@700;800;900&display=swap` |
| Chart.js | `https://cdn.jsdelivr.net/npm/chart.js` |
| SweetAlert2 | `https://cdn.jsdelivr.net/npm/sweetalert2@11` |

---

## Apéndice C — Cómo usar este documento

### Para nuevo template
1. Importa `base.html` o `base_auth.html` (ya cargan Bootstrap + clean_enterprise.css)
2. Usa solo las clases documentadas aquí
3. Aplica los tokens via CSS variables — nunca hardcodees colores hex
4. Si necesitas algo nuevo, propónelo como adición a este documento antes de crearlo en un template

### Para template existente fuera de marca
Ver `AUDIT_INCONSISTENCIAS.md` para el plan de refactor priorizado.

### Para cambios al sistema de diseño
1. Actualizar primero este documento
2. Actualizar `clean_enterprise.css` con las nuevas variables
3. Aplicar al template piloto (landing.html como referencia)
4. Documentar el cambio en CHANGELOG.md

---

**Mantenido por:** equipo Contafy
**Última actualización:** 2026-05-21
