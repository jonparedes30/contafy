# Estrategia de Planes — Contafy

> **Documento de análisis y decisión pendiente.**
> Fecha: 2026 · Estado: borrador para revisión

---

## 📌 Resumen ejecutivo

Contafy ya tiene 3 planes definidos en la landing page (Básico/Pro/Enterprise) pero **no hay diferenciación funcional implementada todavía** — todos los usuarios acceden a todas las features. Este documento analiza 3 estrategias de pricing y monetización para PYMEs latinoamericanas, con una recomendación final.

**TL;DR — Recomendación:** Híbrido (planes estructurados como base + add-ons opcionales en el futuro) con detección automática del plan adecuado al momento del registro.

---

## 🎯 Contexto del problema

### Situación actual
- La landing page ofrece 3 planes con precios ($9.99 / $24.99 / $59.99) pero sin diferenciación real
- El sistema tiene ~15 módulos funcionales (POS, inventario, manufactura, contabilidad NIIF, IA, etc.)
- Stripe está integrado a nivel de infraestructura pero las features no se restringen por plan
- No hay sistema de feature flags

### Audiencia objetivo
PYMEs ecuatorianas/latinoamericanas con diferentes grados de madurez:
- Tiendas y kioscos (necesitan solo facturar)
- Negocios pequeños en crecimiento (necesitan reportes básicos)
- Empresas con contador formal (necesitan NIIF completo)

### Necesidad
Diferenciar funcionalmente los planes para:
1. Justificar el precio incremental
2. Crear path de upgrade claro
3. Comunicar valor a cada segmento de usuario

---

## 🛣️ Las 3 estrategias evaluadas

### Estrategia A — Planes estructurados por madurez de negocio

```
Plan Básico ($9.99)     Plan Pro ($24.99)     Plan Enterprise ($59.99)
─────────────────       ─────────────────     ──────────────────────
POS + Inventario        Todo Básico +         Todo Pro +
Productos               Compras               Contabilidad NIIF
Clientes                Gastos                Depreciación
Reportes operativos     Manufactura           Retenciones SRI
                        Cuentas C/P           4 estados financieros
                        Reportes básicos      Multi-empresa
```

**Cómo funciona:** El usuario elige UN plan al registrarse. Cada plan superior incluye todo lo del inferior + features adicionales.

---

### Estrategia B — Módulos a la carta

```
Usuario arma su plan al registrarse:
☐ POS                       +$5
☐ Inventario               +$3
☐ Manufactura              +$8
☐ Contabilidad NIIF        +$15
☐ Retenciones SRI          +$5
☐ Asistente IA             +$10
☐ Multi-empresa            +$15
☐ ... (15 módulos)
─────────────────────────
Total mensual = suma de módulos elegidos
```

**Cómo funciona:** No hay planes pre-armados. El usuario activa cada módulo individualmente. Pricing es la suma.

---

### Estrategia C — Híbrido (planes + add-ons)

```
PASO 1: Elige un plan base
🥉 Básico ($9.99)  🥈 Pro ($24.99) ⭐  🥇 Enterprise ($59.99)

PASO 2: Agrega add-ons (opcional)
☐ Manufactura ($8)              ← solo si Plan Básico/Pro
☐ Multi-empresa ($15)           ← solo si Plan Pro
☐ API completa ($10)
☐ Asistente IA Premium ($12)
```

**Cómo funciona:** El usuario elige un plan base que cubre el 80% de su uso, y opcionalmente activa add-ons específicos. Combina simplicidad con flexibilidad.

---

## 📊 Comparativa detallada

| Criterio | A: Planes estructurados | B: Módulos a la carta | C: Híbrido |
|---|---|---|---|
| **Decisión del usuario** | ✅ Simple (3 opciones) | ❌ Compleja (15 checkboxes) | ✅ Simple base + opciones |
| **Tiempo de onboarding** | ~30 segundos | 5+ minutos | ~1 minuto |
| **Pricing comunicable** | ✅ "Desde $9.99" | ❌ "Desde X… depende" | ✅ "Desde $9.99 + opcionales" |
| **Conversión inicial estimada** | 8-15% | 4-8% | 7-13% |
| **Revenue expansion** | 🟡 Media (upgrade plan) | ✅ Alta (más módulos) | ✅ Alta (upgrade + add-ons) |
| **Churn** | ✅ Baja | ❌ Alta | 🟡 Media |
| **Flexibilidad real** | ❌ Rígida | ✅ Total | ✅ Suficiente |
| **Soporte/Ventas** | ✅ Sencillo | ❌ Asesoría requerida | 🟡 Documentable |
| **Complejidad técnica** | 🟡 Media | ❌ Alta | 🟡 Media-Alta |
| **Estándar del mercado** | Spotify, Netflix, Slack | SAP, Oracle, HubSpot Ent. | Notion, Stripe, Atlassian |
| **Fit PYMEs latinoamericanas** | ✅ Excelente | ❌ Sobre-ingeniería | ✅ Óptimo |

---

## 🧠 Análisis psicológico del comprador PYME

### Lo que el dueño de tienda Don Pepe NO quiere:
- ❌ Estudiar 15 módulos antes de empezar
- ❌ Decidir si necesita "deterioro NIIF 9" o no
- ❌ Calcular cuánto pagará si activa X+Y+Z
- ❌ Sentir que paga features que no usa
- ❌ Investigar diferencias técnicas entre planes

### Lo que Don Pepe SÍ quiere:
- ✅ "Dame el más barato que sirva para mi tienda"
- ✅ "Si crezco, ¿qué pasa?" (path de upgrade visible)
- ✅ "¿Tiene factura electrónica para el SRI?"
- ✅ Saber el precio total final desde el día 1
- ✅ Poder probar sin compromiso

### Implicación
**Los planes estructurados resuelven esto en 30 segundos. Los módulos lo paralizan.**

Por eso Spotify, Netflix, Slack y la mayoría de SaaS exitosos usan planes estructurados. SAP/Oracle usan módulos a la carta porque su comprador es un CIO con presupuesto millonario que tiene tiempo y un equipo evaluando.

**Las PYMEs latinoamericanas se parecen más al perfil de Spotify/Netflix que al de SAP.**

---

## 💡 Estrategia recomendada: HÍBRIDO

### Distribución sugerida de features por plan

#### 🥉 Plan Básico — $9.99/mes — "Empieza simple"
**Target:** Tiendas, kioscos, pequeños comercios que solo necesitan vender y registrar.

**Incluye:**
- ✅ Productos e inventario simple
- ✅ Ventas (POS rápido tipo caja registradora)
- ✅ Compras simples (sin asientos NIIF complejos)
- ✅ Clientes y proveedores básicos
- ✅ Gastos
- ✅ Reportes operativos (ventas del día/mes, stock, top productos)
- ✅ Dashboard básico
- ✅ Exportación PDF/Excel básica

**Límites:**
- Hasta 100 productos
- 1 usuario
- Sin manufactura
- Sin contabilidad NIIF formal
- Sin asistente IA

**Mensaje:** "Para tu negocio que recién empieza. Vende, controla stock, paga lo justo."

---

#### 🥈 Plan Pro — $24.99/mes — "Mi negocio crece" ⭐ Más popular
**Target:** PYMEs en crecimiento, manufactura pequeña, servicios profesionales.

**Incluye TODO lo de Básico, más:**
- ✅ Manufactura (recetas, materias primas, órdenes de producción)
- ✅ Servicios (catálogo, ventas por servicio)
- ✅ Cuentas por cobrar/pagar con gestión de deudas
- ✅ Estado de Resultados completo
- ✅ Balance General básico
- ✅ Categorías de gastos
- ✅ Asistente IA (consultas básicas)
- ✅ Dashboards rol-específicos (ventas, gastos, inventario)
- ✅ Exportaciones avanzadas

**Límites:**
- Productos ilimitados
- Hasta 5 usuarios
- Sin retenciones SRI
- Sin depreciación automática
- Sin multi-empresa

**Mensaje:** "Tu negocio creció. Suma manufactura, controla deudas, ve reportes profesionales."

---

#### 🥇 Plan Enterprise — $59.99/mes — "Contabilidad profesional"
**Target:** Empresas medianas con contador, listas para auditorías, multi-empresa.

**Incluye TODO lo de Pro, más:**
- ✅ Contabilidad NIIF completa (4 estados financieros)
- ✅ Depreciación automática (NIC 16)
- ✅ Retenciones SRI Ecuador (IVA + IR)
- ✅ Estado de Cambios en Patrimonio
- ✅ Comparativos año anterior
- ✅ NIIF 9 (deterioro), NIIF 15 (contratos), NIC 2 (PEPS)
- ✅ Multi-empresa (gestiona varias razones sociales)
- ✅ API completa
- ✅ Asistente IA Premium (análisis avanzado, predicciones)
- ✅ Notas explicativas NIIF
- ✅ Cierre contable mensual/anual
- ✅ Soporte prioritario
- ✅ Onboarding personalizado
- ✅ Exportar formato SRI (ATS)

**Límites:**
- Usuarios ilimitados
- Multi-empresa ilimitado
- SLA garantizado

**Mensaje:** "Para empresas serias. Cumple NIIF, declara al SRI, audita sin sobresaltos."

---

### Add-ons opcionales (Fase 2 — después del lanzamiento inicial)

```
+ Manufactura ($8/mes)         → Para Plan Básico que necesite producción
+ Multi-empresa ($15/mes)      → Para Plan Pro que gestione varias razones
+ API completa ($10/mes)       → Para Plan Básico/Pro con integraciones
+ Asistente IA Premium ($12/mes) → Para Plan Básico/Pro con análisis avanzado
+ Conciliación bancaria ($7/mes) → Para Plan Pro/Enterprise
+ Almacenamiento extra (+$5/mes)  → Para empresas con muchos archivos
```

**Importante:** Empezar SIN add-ons. Lanzar primero los 3 planes estructurados. Agregar add-ons solo cuando haya usuarios reales pidiendo features que no encajan claramente en un plan.

---

## 🎯 Detección automática del plan (Selección guiada)

Al registrarse, el usuario contesta 2-3 preguntas:

```
PREGUNTA 1: ¿Qué tipo de negocio tienes?
○ Comercio / Tienda          → Sugiere Básico
○ Manufactura / Producción   → Sugiere Pro
○ Servicios profesionales    → Sugiere Pro
○ Múltiples empresas         → Sugiere Enterprise

PREGUNTA 2: ¿Cuántos empleados tienes?
○ Solo yo                    → confirma Básico
○ 2-5                        → sugiere Pro
○ 6-15                       → sugiere Pro o Enterprise
○ 16+                        → sugiere Enterprise

PREGUNTA 3: ¿Necesitas presentar estados financieros NIIF formales?
○ No, solo facturar y vender  → Básico es suficiente
○ Reportes para socios/banco  → Pro es ideal
○ Sí, auditoría externa       → Enterprise

→ Resultado: "Te recomendamos el Plan PRO ($24.99/mes)
  porque tu negocio: tiene manufactura, 3 empleados, y reportes para bancos.
  [Comenzar con Pro]  [Ver comparativa]"
```

**Impacto esperado:** Aumenta conversión 20-30% según data de SaaS B2B.

---

## ⚙️ Implementación técnica (esquema general)

### 1. Modelo `Plan` con `features`

```python
class Plan(models.Model):
    slug = models.CharField(unique=True)
    nombre = models.CharField()
    precio_mensual = models.DecimalField()
    features = models.JSONField(default=dict)
    # Ej: {
    #   "pos": True,
    #   "inventario": True,
    #   "manufactura": False,
    #   "niif_completo": False,
    #   "max_productos": 100,
    #   "max_usuarios": 1,
    #   "multi_empresa": False,
    #   "ia_premium": False,
    #   "retenciones_sri": False,
    # }
```

### 2. Decorator `@require_feature`

```python
@require_feature('manufactura')
def crear_orden_produccion(request):
    # Si el plan no incluye, redirige a página de upgrade
    ...
```

### 3. Template tags para mostrar/ocultar UI

```django
{% if request.user.empresa.suscripcion.tiene_feature 'manufactura' %}
    <a href="/manufactura/">Manufactura</a>
{% else %}
    <a href="/upgrade/?feature=manufactura" class="locked">
        🔒 Manufactura (Plan Pro)
    </a>
{% endif %}
```

### 4. Empty state elegante para features bloqueadas

```
┌────────────────────────────────────────────────┐
│ 🚀  Esta función está en el Plan Pro            │
│                                                 │
│  Manufactura te permitirá:                      │
│  ✓ Gestionar recetas y materias primas         │
│  ✓ Crear órdenes de producción                 │
│  ✓ Calcular costos automáticos                 │
│                                                 │
│  Tus datos muestran que esto te ahorraría      │
│  ~12 horas/mes en cálculos manuales.            │
│                                                 │
│  [Probar Pro 14 días gratis]  [Ver planes]    │
└────────────────────────────────────────────────┘
```

### 5. Modelo `AddOn` (Fase 2)

```python
class AddOn(models.Model):
    slug = models.CharField(unique=True)
    nombre = models.CharField()
    precio_mensual = models.DecimalField()
    feature_clave = models.CharField()
    planes_disponibles = models.ManyToManyField(Plan)

class SuscripcionAddOn(models.Model):
    suscripcion = models.ForeignKey(Suscripcion)
    addon = models.ForeignKey(AddOn)
    activo = models.BooleanField(default=True)
    fecha_activacion = models.DateTimeField()
```

---

## 🛡️ Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Usuarios actuales (beta) se quejan de "perder" features | Alta | Grandfathering: usuarios beta mantienen acceso completo permanente |
| Conversión baja por planes mal distribuidos | Media | A/B test con 2 distribuciones diferentes, medir 60 días |
| Ingresos iniciales bajos por todos en Básico | Media | Plan Básico debe ser **realmente limitado** para incentivar upgrade |
| Complejidad técnica al implementar feature flags | Baja | Usar django-flags o package similar (estándar) |
| Difícil decidir qué features van en qué plan | Alta | Este documento + iterar con datos reales después |
| Usuarios cancelan al ver que su feature ya no está | Media | Avisar con 30 días antes + ofrecer descuento de upgrade |

---

## 📅 Plan de adopción sugerido

### Fase 1 — Lanzamiento (semana 1-2)
- [ ] Aprobar la distribución de features por plan
- [ ] Crear modelo `Plan` con `features` JSONField
- [ ] Poblar los 3 planes con sus features
- [ ] Implementar decorator `@require_feature`
- [ ] Implementar template tag `tiene_feature`
- [ ] Migrar las URLs/vistas principales para usar el decorator

### Fase 2 — Diferenciación UI (semana 2-3)
- [ ] Ocultar/mostrar menús del sidebar según plan
- [ ] Crear empty states bonitos para features bloqueadas
- [ ] Página de comparativa de planes detallada
- [ ] Página de upgrade con un click

### Fase 3 — Selección guiada (semana 3-4)
- [ ] Wizard de 3 preguntas al registrar
- [ ] Recomendación automática de plan
- [ ] Banner sticky "Tu plan Pro está activo · Próxima cobranza: X"

### Fase 4 — Grandfathering (semana 4)
- [ ] Migración de usuarios beta existentes
- [ ] Comunicación por email explicando cambios
- [ ] Activar restricción para usuarios nuevos

### Fase 5 — Add-ons (mes 3+, opcional)
- [ ] Modelo `AddOn` y `SuscripcionAddOn`
- [ ] UI para activar add-ons sobre cualquier plan
- [ ] Billing en Stripe con line-items adicionales

---

## ❓ Decisiones pendientes

Antes de implementar, hay que decidir:

1. **¿Estrategia híbrida o solo planes estructurados?**
   - Híbrido es más flexible pero más complejo
   - Estructurados puros es más simple y más rápido al mercado

2. **¿La distribución sugerida está bien?**
   - ¿Manufactura debe estar en Básico también?
   - ¿NIIF básico debe estar en Pro?
   - ¿Qué tan limitado debe ser Básico?

3. **¿Grandfathering para usuarios beta?**
   - ¿Mantener acceso completo permanente?
   - ¿Por cuánto tiempo?

4. **¿Trial gratuito?**
   - ¿14 días con Pro/Enterprise gratis?
   - ¿Sin tarjeta de crédito?

5. **¿Selección guiada al registrar?**
   - ¿Vale la pena el desarrollo extra?
   - O dejar que el usuario elija directo el plan

6. **¿Roadmap de add-ons?**
   - ¿Cuáles add-ons lanzar primero (Fase 2)?
   - ¿Precio de cada add-on?

---

## 🎯 Recomendación final consolidada

| Aspecto | Recomendación |
|---|---|
| **Estrategia** | Híbrido (planes estructurados + add-ons en Fase 2) |
| **Lanzar primero** | Solo los 3 planes estructurados |
| **Selección guiada** | Sí, agregar al wizard de registro (alto ROI) |
| **Trial gratuito** | Sí, 14 días Pro sin tarjeta |
| **Grandfathering** | Sí, usuarios beta mantienen acceso por 12 meses |
| **Distribución** | La sugerida en este documento |
| **Add-ons (Fase 2)** | Solo cuando haya 50+ usuarios pagos y se pida algún módulo específico |

---

## 📎 Recursos para profundizar

- Patrick Campbell (ProfitWell): "SaaS Pricing Strategy"
- "Monetizing Innovation" — Madhavan Ramanujam (libro)
- Casos de estudio: cómo Shopify, Wix, Square segmentan PYMEs
- Datos del SRI Ecuador para validar segmentación por tipo de negocio
