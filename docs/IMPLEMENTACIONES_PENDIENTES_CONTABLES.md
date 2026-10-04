# Implementaciones Contables Pendientes — Contafy

> **Documento de roadmap contable/NIIF.**
> Fecha: 2026 · Estado: pendiente de priorización

---

## 📌 Resumen ejecutivo

El sistema contable de Contafy ya cumple con los principios fundamentales (partida doble, cuadre 100%, asientos automáticos en ventas/compras/gastos, IVA correcto, estados financieros básicos). Sin embargo, existen **9 funcionalidades NIIF/fiscales** que faltan para que el sistema sea **completo a nivel profesional** y cumpla con las exigencias del SRI Ecuador y de auditorías externas.

**Estado actual:**
- ✅ Partida doble con cuadre garantizado
- ✅ 3 estados financieros básicos (Balance, Resultados, Flujo simple)
- ✅ NIIF 9 (deterioro CxC), NIIF 15 (contratos), NIC 2 (PEPS)
- ❌ Sin depreciación de activos fijos
- ❌ Sin retenciones SRI
- ❌ Sin 4to estado financiero (Cambios en Patrimonio)
- ❌ Sin comparativos año anterior

---

## 🎯 Estado actual del sistema contable

### Lo que YA funciona

| Funcionalidad | Estado | Detalle |
|---|---|---|
| Partida doble | ✅ | Validada con context manager `agrupar_transaccion()` |
| Cuadre automático | ✅ | 100% en todas las empresas (verificado con `verificar_cuadre`) |
| Asientos en Venta | ✅ | Auto + sincronización en edit/delete |
| Asientos en Compra | ✅ | Auto + sincronización en edit/delete |
| Asientos en Gasto | ✅ | Auto + sincronización en edit/delete |
| Cálculo IVA | ✅ | Con `Decimal` y `ROUND_HALF_UP` |
| Estado de Resultados | ✅ | Con cascada NIIF + impuestos Ecuador (15% PT + 25% IR) |
| Balance General | ✅ | Con clasificación corriente/no corriente |
| Flujo de Caja | ⚠️ | Existe pero simple (sin método directo NIIF) |
| NIIF 9 — Deterioro CxC | ✅ | Modelo + cálculo automático |
| NIIF 15 — Contratos | ✅ | Modelo `ContratoVenta` y `ObligacionDesempeño` |
| NIC 2 — Inventarios PEPS | ✅ | Modelo `MovimientoInventario` con costo PEPS |
| Verificador de integridad | ✅ | Comando `verificar_cuadre` con reparación automática |

### Lo que FALTA

| # | Funcionalidad | Categoría | Prioridad |
|---|---|---|---|
| 1 | Depreciación automática (NIC 16) | NIIF crítica | 🔴 Alta |
| 2 | Retenciones SRI Ecuador (IVA + IR) | Fiscal obligatoria | 🔴 Alta |
| 3 | Estado de Cambios en el Patrimonio | NIIF crítica | 🔴 Alta |
| 4 | Comparativos año anterior | NIIF obligatoria | 🟡 Media |
| 5 | Campo `clasificacion_niif` explícito | Calidad | 🟢 Baja |
| 6 | Cierre contable mensual | Calidad | 🟡 Media |
| 7 | Conciliación bancaria | Funcional | 🟡 Media |
| 8 | Notas explicativas completas | NIIF | 🟢 Baja |
| 9 | Exportar formato SRI (ATS) | Fiscal | 🟢 Baja |

---

## 🔴 Mejoras CRÍTICAS NIIF/Fiscales

### 1️⃣ Depreciación automática de activos fijos (NIC 16)

#### ¿Qué es?
Los activos fijos (Maquinaria, Equipos, Vehículos, Edificios, Muebles) pierden valor con el tiempo por uso y desgaste. NIC 16 obliga registrar esa pérdida mensualmente como un gasto llamado **"depreciación"**.

#### ¿Por qué importa?
- Sin depreciación, los activos quedan inflados artificialmente en el balance
- Las utilidades reportadas quedan infladas (no se descuenta el desgaste)
- En auditoría o declaración tributaria SRI esto se detecta inmediatamente
- Es un principio contable básico, casi universal

#### Ejemplo concreto
```
Empresa compra Maquinaria por $1,000
Vida útil: 10 años (NIC 16 recomienda según tipo de activo)
Método: Línea recta (más común)
Depreciación mensual: $1,000 / (10 × 12) = $8.33/mes
Depreciación anual: $100/año

Asiento mensual automático:
  Débito  Gasto Depreciación        $8.33
  Crédito Depreciación Acumulada   ($8.33)

Después de 5 años en el balance:
  Activo Fijo (Maquinaria):                $1,000
  (-) Depreciación Acumulada:                $500
  = Valor neto en libros:                    $500
```

#### Métodos NIC 16 soportados
| Método | Cuándo se usa |
|---|---|
| **Línea recta** | El más común. Mismo monto cada año. |
| **Saldos decrecientes** | Activos que pierden más valor al inicio (ej. vehículos). |
| **Unidades de producción** | Maquinaria que se mide por uso (ej. kilómetros). |

#### Vida útil típica (sugerida por SRI/NIIF)
- Edificios: 20-50 años
- Vehículos: 5 años
- Muebles y enseres: 10 años
- Maquinaria: 10-15 años
- Equipos de cómputo: 3-5 años

#### Qué se construye técnicamente

**Modelo `ActivoFijo`:**
```python
class ActivoFijo(AuditModel):
    METODOS = [('linea_recta', 'Línea Recta'),
               ('saldos_decrecientes', 'Saldos Decrecientes'),
               ('unidades', 'Unidades de Producción')]

    empresa = ForeignKey(Empresa)
    nombre = CharField()
    descripcion = TextField()
    costo_adquisicion = DecimalField()
    fecha_adquisicion = DateField()
    vida_util_anios = IntegerField()
    valor_residual = DecimalField(default=0)
    metodo_depreciacion = CharField(choices=METODOS)
    cuenta_activo = ForeignKey(CuentaContable)  # ej. "Maquinaria"
    cuenta_depreciacion = ForeignKey(CuentaContable)  # ej. "Dep. Acumulada Maquinaria"

    def calcular_depreciacion_mensual(self):
        if self.metodo_depreciacion == 'linea_recta':
            depreciable = self.costo_adquisicion - self.valor_residual
            return depreciable / (self.vida_util_anios * 12)
        # ... otros métodos

    @property
    def valor_neto_libros(self):
        dep_acumulada = self.depreciaciones.aggregate(t=Sum('monto'))['t'] or 0
        return self.costo_adquisicion - dep_acumulada
```

**Comando management:**
```python
# python manage.py calcular_depreciacion_mensual
class Command(BaseCommand):
    def handle(self, *args, **options):
        hoy = date.today()
        for activo in ActivoFijo.objects.filter(activo=True):
            # Verificar si ya se calculó este mes
            if not activo.depreciaciones.filter(
                fecha__year=hoy.year, fecha__month=hoy.month
            ).exists():
                monto = activo.calcular_depreciacion_mensual()
                with MovimientoContable.agrupar_transaccion(
                    f'Depreciación mensual {activo.nombre}'
                ):
                    # Débito: Gasto Depreciación
                    # Crédito: Depreciación Acumulada
                    ...
```

**Cron job (opcional):** Configurar para que corra automáticamente cada día 1 del mes.

**UI:**
- Vista `listar_activos_fijos`
- Vista `crear_activo_fijo` (formulario)
- Vista `detalle_activo_fijo` (tabla de depreciaciones mensuales)
- En balance: mostrar "Activo Fijo $1,000 (-) Dep. Acumulada $500 = Valor neto $500"

**Esfuerzo:** ~1.5-2h
**Riesgo:** Bajo (funcionalidad nueva, no toca código existente)
**Beneficio:** Balance refleja valor real de activos · cumplimiento NIC 16

---

### 2️⃣ Retenciones SRI Ecuador (IVA + IR)

#### ¿Qué es?
En Ecuador, cuando un contribuyente le paga a otro, debe **retener** parte del IVA y del Impuesto a la Renta para entregárselo directamente al SRI (Servicio de Rentas Internas).

#### Tipos de retención

**Retención IVA:**
| Porcentaje | Cuándo aplica |
|---|---|
| 30% | Compras de bienes |
| 70% | Servicios entre contribuyentes |
| 100% | Servicios profesionales, arriendos, pagos al exterior |

**Retención IR (Impuesto a la Renta):**
| Porcentaje | Concepto |
|---|---|
| 1% | Compra de bienes muebles |
| 2% | Servicios entre sociedades |
| 5% | Honorarios entre sociedades |
| 8% | Honorarios profesionales |
| 10% | Honorarios artísticos |

#### ¿Por qué importa?
- **Obligación legal ineludible en Ecuador**
- Multas significativas por no efectuar retenciones
- Afecta directamente el flujo de caja (lo que sale del banco es menor al monto total)
- El balance debe mostrar "Retenciones por pagar al SRI" como pasivo corriente
- Se deben presentar mensualmente al SRI (Formulario 103 / 104 / ATS)

#### Ejemplo concreto
```
Compra de servicio profesional (honorarios contable):
  Monto neto:                          $1,000
  IVA 15%:                               $150
  Total factura:                       $1,150

Retenciones que debe efectuar el comprador:
  Retención IVA 100%:                  ($150)  ← se queda con el IVA
  Retención IR 10% (s/ monto neto):   ($100)
  ────────────────────────────────────────
  Lo que paga al proveedor:             $900
  Pendiente entregar al SRI:            $250

Asientos contables:
  Débito  Gasto Honorarios:           $1,000
  Débito  IVA Crédito Fiscal:           $150  (lo retuvo, no lo paga al prov.)
  Crédito Retención IVA por Pagar:    ($150)  (pasivo corriente al SRI)
  Crédito Retención IR por Pagar:     ($100)  (pasivo corriente al SRI)
  Crédito Caja/Bancos:                ($900)  (lo que sale)
```

#### Qué se construye técnicamente

**Modelo `RetencionConfig` (catálogo):**
```python
class PorcentajeRetencion(models.Model):
    TIPOS = [('iva', 'IVA'), ('ir', 'Impuesto a la Renta')]
    tipo = CharField(choices=TIPOS)
    codigo_sri = CharField()  # código oficial del SRI
    concepto = CharField()    # "Honorarios profesionales", etc.
    porcentaje = DecimalField()
    activo = BooleanField(default=True)
```

**Modificar `Compra`:**
```python
class Compra(AuditModel):
    # ... campos existentes ...

    # Nuevos campos:
    aplica_retencion_iva = BooleanField(default=False)
    retencion_iva_porcentaje = ForeignKey(PorcentajeRetencion, ...)
    retencion_iva_monto = DecimalField(default=0)

    aplica_retencion_ir = BooleanField(default=False)
    retencion_ir_porcentaje = ForeignKey(PorcentajeRetencion, ...)
    retencion_ir_monto = DecimalField(default=0)

    @property
    def monto_a_pagar_proveedor(self):
        """Monto real que sale de caja después de retenciones"""
        return self.monto - self.retencion_iva_monto - self.retencion_ir_monto
```

**Modificar `ContabilidadService.crear_asientos_compra`:**
Generar asientos adicionales para las retenciones cuando apliquen.

**Vista nueva: Comprobante de Retención**
- Generar PDF del comprobante de retención emitido al proveedor
- Cumple formato del SRI Ecuador

**Reporte mensual: Resumen de retenciones**
- Lista todas las retenciones del mes
- Total a pagar al SRI por concepto
- Exportable a formato SRI

**Esfuerzo:** ~2-3h (es funcionalidad fiscal compleja)
**Riesgo:** Medio (modifica el flujo central de compras)
**Beneficio:** Cumplimiento legal Ecuador · flujo de caja correcto

---

### 3️⃣ Estado de Cambios en el Patrimonio (4to estado financiero NIIF)

#### ¿Qué es?
NIIF exige presentar **4 estados financieros** completos:

1. ✅ **Estado de Situación Financiera** (Balance) — Implementado
2. ✅ **Estado de Resultados** — Implementado
3. ❌ **Estado de Cambios en el Patrimonio** — FALTA
4. ⚠️ **Estado de Flujos de Efectivo** — Existe pero simple

El Estado de Cambios en el Patrimonio muestra **cómo cambió el patrimonio (capital + reservas + utilidades) durante el período**.

#### ¿Por qué importa?
- **NIIF lo exige** explícitamente — sin esto, los estados financieros están "incompletos"
- Bancos lo piden para evaluar solicitudes de crédito
- Auditorías externas lo requieren
- Muestra de dónde vino y a dónde fue el dinero de los socios/dueños

#### Ejemplo concreto

```
ESTADO DE CAMBIOS EN EL PATRIMONIO
Período: Enero 2024 - Diciembre 2024

                                      Capital     Utilidades    Sup. de       Total
                                      Social      Acumuladas    Revaluación   Patrimonio
                                      ─────────   ──────────    ───────────   ──────────
Saldo inicial (1 enero 2024):         $10,000        $5,000         $1,500     $16,500
+ Aportes de capital socios:           $5,000             0              0      $5,000
+ Utilidad neta del período:                0        $3,500              0      $3,500
- Retiros de socios:                  ($1,000)            0              0     ($1,000)
+ Superávit por revaluación:                0             0           $500        $500
- Distribución de dividendos:               0       ($2,000)             0     ($2,000)
                                      ─────────   ──────────    ───────────   ──────────
Saldo final (31 diciembre 2024):      $14,000        $6,500         $2,000     $22,500
```

#### Datos necesarios (ya disponibles en el sistema)
- **Aportes y retiros:** del modelo `Capital`
- **Utilidad del período:** del Estado de Resultados (vista existente)
- **Revaluación:** del modelo `RevaluacionActivo`
- **Distribuciones de dividendos:** TODO — agregar modelo si no existe

#### Qué se construye técnicamente

**Vista nueva:**
```python
@login_required
def estado_cambios_patrimonio(request):
    empresa = request.user.empresa
    fecha_inicio, fecha_fin = ...  # de filtros

    # 1. Saldo inicial de cada cuenta de patrimonio
    saldo_inicial = ...  # consultar MovimientoContable hasta fecha_inicio - 1

    # 2. Movimientos del período
    aportes = Capital.objects.filter(
        empresa=empresa, tipo='aporte',
        fecha__range=[fecha_inicio, fecha_fin]
    ).aggregate(t=Sum('monto'))['t'] or 0

    retiros = Capital.objects.filter(...)

    utilidad_neta = ReportesNIIFService.calcular_utilidad_neta(
        empresa, fecha_inicio, fecha_fin
    )

    revaluaciones = RevaluacionActivo.objects.filter(...)

    # 3. Saldo final
    saldo_final = saldo_inicial + aportes - retiros + utilidad_neta + revaluaciones

    return render(request, 'empresa/niif/estado_cambios_patrimonio.html', {
        'saldo_inicial': saldo_inicial,
        'aportes': aportes,
        'retiros': retiros,
        'utilidad_neta': utilidad_neta,
        'revaluaciones': revaluaciones,
        'saldo_final': saldo_final,
    })
```

**Template:** Tabla con las columnas mostradas en el ejemplo + total.

**URL:** `/app-beta-2024/niif/estado-cambios-patrimonio/`

**Menú:** Agregar al sidebar bajo "Finanzas"

**Esfuerzo:** ~45 min - 1h
**Riesgo:** Bajo (solo lectura de datos existentes)
**Beneficio:** Completa los 4 estados financieros NIIF obligatorios

---

### 4️⃣ Comparativos año anterior

#### ¿Qué es?
NIIF exige presentar cada estado financiero con la **columna del período anterior comparativa**, para que el lector pueda ver la evolución.

#### ¿Por qué importa?
- NIIF lo requiere explícitamente
- Es lo que esperan ver auditores, bancos y socios
- Permite análisis de tendencias y variaciones
- Detecta anomalías (ej. "ventas cayeron 30% vs año pasado")

#### Ejemplo concreto

**Estado de Resultados con comparativo:**
```
                                       2024          2023        Δ %
                                      ─────         ─────       ─────
Ventas                              $50,000       $42,000        +19%
Costo de Ventas                    ($30,000)    ($25,000)        +20%
Utilidad Bruta                      $20,000       $17,000        +18%
Gastos Operativos                  ($10,000)     ($9,000)        +11%
Utilidad Operativa                  $10,000       $8,000         +25%
Impuestos                          ($3,500)      ($2,800)        +25%
Utilidad Neta                        $6,500       $5,200         +25%
```

**Balance General con comparativo:**
```
                                  Dic 2024      Dic 2023        Δ
                                  ───────       ───────        ───
ACTIVOS
  Activos Corrientes               $25,000       $20,000      +25%
  Activos No Corrientes             $5,000        $3,000      +67%
  TOTAL ACTIVOS                    $30,000       $23,000      +30%

PASIVOS
  Pasivos Corrientes                $5,000        $4,000      +25%
  Pasivos No Corrientes             $2,500        $2,500        0%
  TOTAL PASIVOS                     $7,500        $6,500      +15%

PATRIMONIO                         $22,500       $16,500      +36%
```

#### Qué se construye técnicamente

**Modificar vistas existentes:**
```python
def estado_resultados_simple(request):
    # ... lógica actual ...

    # Calcular también período anterior
    año_anterior_inicio = fecha_inicio - relativedelta(years=1)
    año_anterior_fin = fecha_fin - relativedelta(years=1)

    datos_actual = calcular_estado_resultados(empresa, fecha_inicio, fecha_fin)
    datos_anterior = calcular_estado_resultados(empresa, año_anterior_inicio, año_anterior_fin)

    # Calcular variaciones %
    variaciones = {
        'ventas': calcular_variacion(datos_actual['ventas'], datos_anterior['ventas']),
        # ...
    }

    context = {
        'actual': datos_actual,
        'anterior': datos_anterior,
        'variaciones': variaciones,
    }
```

**Modificar templates:** Agregar columnas "Período Anterior" y "Δ%" en las tablas.

**Toggle opcional:** Botón "Mostrar/Ocultar comparativo año anterior" (para no saturar la UI).

**Esfuerzo:** ~1h
**Riesgo:** Bajo (es agregar datos, no modificar)
**Beneficio:** NIIF completo + análisis de tendencias

---

## 🟢 Mejoras de calidad

### 5️⃣ Campo `clasificacion_niif` en `CuentaContable`

#### ¿Qué es?
Reemplazar la **heurística por nombre** actual con un **campo explícito** que el usuario controle.

**Hoy:**
```python
def es_activo_corriente(nombre):
    n = nombre.lower()
    return n.startswith('caja') or n.startswith('banco') or ...  # heurística frágil
```

**Después:**
```python
class CuentaContable(models.Model):
    # ... campos existentes ...
    clasificacion_niif = CharField(choices=[
        ('activo_corriente', 'Activo Corriente'),
        ('activo_no_corriente', 'Activo No Corriente'),
        ('pasivo_corriente', 'Pasivo Corriente'),
        ('pasivo_no_corriente', 'Pasivo No Corriente'),
        ('patrimonio', 'Patrimonio'),
        ('ingreso', 'Ingreso'),
        ('costo', 'Costo'),
        ('gasto', 'Gasto'),
    ])
```

#### ¿Por qué importa?
- Robustez: si usuario crea "Bancos Pichincha" o "Inversiones Largo Plazo", la clasificación está garantizada
- Permite cuentas customizadas sin romper reportes
- Mejor experiencia: usuario decide explícitamente

#### Migración
Para empresas existentes, hacer migración que asigne `clasificacion_niif` automáticamente usando la heurística actual. Datos legacy quedan correctos.

**Esfuerzo:** ~45 min
**Riesgo:** Bajo (migración + cambio simple en reportes)

---

### 6️⃣ Cierre contable mensual

#### ¿Qué es?
Al finalizar cada mes, "cerrar" las cuentas de ingresos y gastos transfiriéndolas a una cuenta de utilidad acumulada.

#### Proceso
```
Al cierre del mes:
1. Calcular utilidad neta del mes
2. Cerrar cuentas de ingresos:
   Débito  Ingresos por Ventas:     $10,000
   Crédito Resumen Utilidades:     ($10,000)

3. Cerrar cuentas de gastos:
   Débito  Resumen Utilidades:       $3,500
   Crédito Gastos Operativos:      ($3,500)
   Crédito Costo de Ventas:        ($X,XXX)

4. Transferir a Utilidades Acumuladas:
   Débito  Resumen Utilidades:       $6,500
   Crédito Utilidades Acumuladas:  ($6,500)
```

#### ¿Por qué importa?
- Práctica contable estándar
- Acelera reportes (no recalcular desde inicio del tiempo)
- Permite ver utilidad por mes histórico fácilmente
- Necesario para cierre anual NIIF

**Esfuerzo:** ~1h
**Riesgo:** Medio (modifica cuentas contables; debe ser reversible)

---

### 7️⃣ Conciliación bancaria

#### ¿Qué es?
Subir extracto bancario (PDF/Excel) y conciliar con los movimientos de Caja/Bancos del sistema.

#### Flujo
```
1. Usuario sube extracto del banco (CSV o PDF)
2. Sistema parsea los movimientos del extracto
3. Sistema cruza cada movimiento con MovimientoContable de Caja/Bancos
4. Muestra:
   - ✅ Conciliados (montos y fechas coinciden)
   - ⚠️ Solo en banco (no registrado en sistema)
   - ⚠️ Solo en sistema (no aparece en banco)
5. Usuario marca cada uno como conciliado/excepción
```

#### ¿Por qué importa?
- Detecta errores y fraudes
- Funcionalidad estándar de cualquier ERP
- Facilita el cierre mensual
- Auditorías la exigen

**Esfuerzo:** ~3-4h (es feature compleja con parsers)
**Riesgo:** Medio

---

### 8️⃣ Notas explicativas más completas

#### ¿Qué es?
Las notas a los estados financieros son **documentos extensos que explican las políticas contables, métodos de medición, y detalles** que no caben en los estados resumen.

NIIF exige docenas de notas según el tamaño de la empresa:
- Política de reconocimiento de ingresos (NIIF 15)
- Política de inventarios (PEPS/promedio)
- Vida útil de activos fijos (NIC 16)
- Política de deterioro de cuentas por cobrar (NIIF 9)
- Compromisos contractuales
- Hechos posteriores al cierre
- Etc.

#### ¿Por qué importa?
- NIIF lo exige
- Auditorías lo piden
- Bancos lo evalúan

#### Estado actual
Existe `notas_explicativas.html` con una versión básica. Falta:
- Editor de notas (rich text)
- Plantillas pre-armadas según tipo de empresa
- Numeración automática
- Exportación a PDF profesional

**Esfuerzo:** ~1.5h
**Riesgo:** Bajo

---

### 9️⃣ Exportar formato SRI Ecuador (ATS)

#### ¿Qué es?
**ATS = Anexo Transaccional Simplificado** — formato XML que el SRI Ecuador requiere mensualmente para reportar:
- Compras efectuadas
- Ventas realizadas
- Retenciones efectuadas
- Importaciones y exportaciones

#### ¿Por qué importa?
- Obligación mensual con el SRI
- Hoy se hace manualmente (Excel → conversión → XML)
- Genera errores
- Es trabajo manual repetitivo

#### Qué se construye
- Vista que genera el XML según el formato exacto del SRI
- Validación de datos antes de exportar
- Botón "Descargar ATS Mes/Año" en el menú de exportaciones

**Esfuerzo:** ~3-4h (formato XML específico, validaciones)
**Riesgo:** Medio (formatos SRI son estrictos; cualquier error rechaza el archivo)

---

## 📊 Priorización recomendada

### 🥇 Fase 1: NIIF crítico (esfuerzo 3-4h)

**Objetivo:** Completar los estados financieros NIIF obligatorios.

| # | Mejora | Esfuerzo | Por qué primero |
|---|---|---|---|
| 3 | Estado de Cambios en Patrimonio | 45 min | Más rápido, completa NIIF |
| 4 | Comparativos año anterior | 1h | NIIF lo exige, bajo riesgo |
| 1 | Depreciación automática | 1.5-2h | Sin esto los activos quedan inflados |

**Resultado:** Sistema cumple NIIF al 100% en estados financieros básicos.

---

### 🥈 Fase 2: Fiscal Ecuador (esfuerzo 2-3h)

**Objetivo:** Cumplir obligaciones legales con el SRI.

| # | Mejora | Esfuerzo | Por qué |
|---|---|---|---|
| 2 | Retenciones SRI (IVA + IR) | 2-3h | Obligación legal Ecuador |

**Resultado:** Sistema permite operar legalmente en Ecuador sin multas.

---

### 🥉 Fase 3: Calidad y robustez (esfuerzo 2-3h)

**Objetivo:** Mejorar mantenibilidad y experiencia.

| # | Mejora | Esfuerzo | Por qué |
|---|---|---|---|
| 5 | Campo `clasificacion_niif` | 45 min | Más robusto que heurística |
| 6 | Cierre contable mensual | 1h | Acelera reportes históricos |
| 8 | Notas explicativas | 1.5h | Completa los documentos |

---

### 🏅 Fase 4: Avanzados (esfuerzo 6-8h)

**Objetivo:** Features avanzadas para empresas grandes.

| # | Mejora | Esfuerzo | Por qué |
|---|---|---|---|
| 7 | Conciliación bancaria | 3-4h | Funcionalidad de ERP enterprise |
| 9 | Exportar formato ATS SRI | 3-4h | Automatiza trabajo manual |

---

## 🎯 Recomendación final

**Empezar por Fase 1 completa (3-4h)** porque:
1. Completa NIIF obligatorio
2. Esfuerzo bajo
3. Beneficio inmediato (estados financieros correctos)
4. Cero riesgo de regresiones

**Después decidir Fase 2 según urgencia legal:**
- Si hay usuarios con declaraciones pendientes → Fase 2 inmediato
- Si todavía es desarrollo/beta → Fase 3 antes (mejorar calidad)

**Fase 4 puede esperar a tener usuarios pagos:**
- Conciliación bancaria es deseable pero no crítico
- ATS SRI solo lo necesitan empresas grandes (~1% de usuarios típicamente)

---

## 🛡️ Riesgos transversales

| Riesgo | Cómo mitigarlo |
|---|---|
| Romper el cuadre al agregar features | Cada cambio se valida con `python manage.py verificar_cuadre` |
| Migrations destruyen datos | Todos los campos nuevos son `null=True, blank=True` |
| Usuarios beta no entienden nuevas features | Agregar tooltips + documentación inline |
| Cálculos NIIF tienen errores | Validar con casos de prueba reales + revisión de contador |
| Cambios en normativa SRI | Tasas y porcentajes en `PorcentajeRetencion` (config) no hardcoded |

---

## 📎 Recursos para profundizar

### NIIF
- IFRS Foundation — [www.ifrs.org](https://www.ifrs.org) (textos oficiales)
- NIC 16 — Propiedades, Planta y Equipo
- NIIF 9 — Instrumentos Financieros (ya implementado)
- NIIF 15 — Ingresos de Contratos con Clientes (ya implementado)
- NIC 2 — Inventarios (ya implementado)

### Ecuador / SRI
- SRI — [www.sri.gob.ec](https://www.sri.gob.ec) (formularios oficiales)
- Resoluciones NAC-DGERCGC sobre retenciones (vigentes)
- Guía oficial ATS (Anexo Transaccional Simplificado)
- Reglamento LRTI (Ley de Régimen Tributario Interno)

### Implementación
- Django ORM transactions: documentación oficial
- Decimal en Python para precisión monetaria
- django-extensions para signals contables

---

## 📝 Decisiones pendientes

Antes de implementar, se debe decidir:

1. **¿Cuáles fases atacar y en qué orden?**
2. **¿En qué plan(es) incluir cada feature?** (ver `docs/ESTRATEGIA_PLANES.md`)
3. **¿Quién valida los cálculos NIIF?** (idealmente un contador externo)
4. **¿Se requiere certificación NIIF/SRI?** (depende del mercado objetivo)
5. **¿Multi-país?** (si sí, externalizar tasas y normativas a configuración)

---

## ✅ Checklist consolidado

- [ ] Decidir prioridad (Fase 1 recomendada como inicio)
- [ ] Validar distribución por plan con `docs/ESTRATEGIA_PLANES.md`
- [ ] Implementar Fase 1 (Estado Cambios Patrimonio + Comparativos + Depreciación)
- [ ] Validar con casos reales (idealmente revisión de contador)
- [ ] Implementar Fase 2 (Retenciones SRI) si hay urgencia legal
- [ ] Implementar Fase 3 (Calidad) antes de salir a producción
- [ ] Fase 4 (Conciliación + ATS) según necesidad de usuarios
