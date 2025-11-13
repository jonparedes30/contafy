# Development Guidelines - CONTAFY

## Code Quality Standards

### File Organization
- **Separation of Concerns**: Models, services, views, and utilities are strictly separated into dedicated modules
- **Service Layer Pattern**: Business logic is encapsulated in service classes (e.g., `GamificacionService`, `SimulacionService`, `ContabilidadService`)
- **Model Splitting**: Large model files are split by domain (e.g., `models.py`, `models_aprendizaje.py`, `models_gamificacion.py`, `models_simulaciones.py`)
- **Utility Modules**: Helper functions grouped by purpose (`money.py`, `normalizador.py`, `security.py`)

### Naming Conventions
- **Spanish Language**: All model names, field names, and business logic use Spanish terminology (e.g., `Empresa`, `Venta`, `Gasto`, `CuentaContable`)
- **Descriptive Names**: Variables and methods use clear, descriptive names (e.g., `obtener_datos_empresa`, `calcular_deterioro_niif9`, `crear_asientos_contables`)
- **Snake Case**: Python convention for functions and variables (`crear_asientos_contables`, `datos_usuario`)
- **PascalCase**: Django convention for model classes (`MovimientoContable`, `SimulacionUsuario`)

### Documentation Standards
- **Docstrings**: All service methods include docstrings explaining purpose
  ```python
  def procesar_simulacion_venta(simulacion, datos_usuario, modo_sandbox=True):
      """Procesa una simulación de venta (para comercio)"""
  ```
- **Inline Comments**: Complex business logic includes explanatory comments (e.g., NIIF calculations, accounting rules)
- **Type Hints**: Not consistently used, but Decimal types are explicitly handled for financial calculations

### Code Formatting
- **Line Length**: Generally follows PEP 8 (80-100 characters), with some exceptions for readability
- **Indentation**: 4 spaces (Python standard)
- **Imports**: Organized with Django imports first, then third-party, then local
- **String Quotes**: Single quotes for strings, double quotes for docstrings

## Semantic Patterns

### Service Pattern (Highly Prevalent)
Business logic is encapsulated in static service classes:

```python
class SimulacionService:
    @staticmethod
    def iniciar_simulacion(usuario, tipo_simulacion_id, leccion=None, modo_sandbox=False):
        """Inicia una nueva simulación para el usuario"""
        # Business logic here
        return simulacion
```

**Frequency**: Used in 15+ service files
**Purpose**: Separate business logic from views and models

### Audit Pattern
Models inherit from `AuditModel` for automatic tracking:

```python
class AuditModel(models.Model):
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    modificado_por = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        user = get_current_user()
        if not self.pk:
            self.creado_por = user
        else:
            self.modificado_por = user
        super().save(*args, **kwargs)
```

**Frequency**: Used in 20+ models
**Purpose**: Track who created/modified records and when

### Automatic Accounting Pattern
Models automatically create double-entry bookkeeping on save:

```python
def save(self, *args, **kwargs):
    es_nuevo = not self.pk
    super().save(*args, **kwargs)
    
    if es_nuevo:
        self.crear_asientos_contables()
        self.crear_cuenta_por_cobrar_si_credito()
```

**Frequency**: Used in Venta, Compra, Gasto, Capital models
**Purpose**: Ensure accounting integrity without manual intervention

### Sandbox Execution Pattern
Simulations run in isolated transactions that can be rolled back:

```python
if modo_sandbox:
    with transaction.atomic():
        sp = transaction.savepoint()
        try:
            enable_sandbox()
            # Execute simulation logic
            # Validate results
        except Exception as e:
            resultado['sandbox_error'] = str(e)
        finally:
            disable_sandbox()
            transaction.savepoint_rollback(sp)
```

**Frequency**: Used in all simulation services
**Purpose**: Test scenarios without affecting real data

### Decimal Precision Pattern
All financial calculations use Decimal for precision:

```python
from decimal import Decimal, ROUND_HALF_UP

subtotal = quantize_currency(to_decimal(cantidad) * to_decimal(precio_unitario))
iva = quantize_currency(subtotal * to_decimal('0.12'))
total = quantize_currency(subtotal + iva)
```

**Frequency**: Used in 100+ locations across models and services
**Purpose**: Avoid floating-point precision errors in financial calculations

### Property-Based Calculations
Models use `@property` for computed values:

```python
@property
def margen_ganancia(self):
    """Calcula el margen de ganancia del producto"""
    if self.precio_venta > 0 and self.precio_costo > 0:
        return ((self.precio_venta - self.precio_costo) / self.precio_venta) * 100
    return 0
```

**Frequency**: Used in 30+ models
**Purpose**: Provide calculated values without storing redundant data

### Normalization Pattern
Business data is normalized for consistency:

```python
def normalizar_tipo_negocio(tipo_negocio, categoria):
    """Normaliza el tipo de negocio para benchmarking"""
    mapeo_comercial = {
        'licoreria': ['licorería', 'licoreria', 'venta de licores'],
        'farmacia': ['farmacia', 'botica', 'droguería'],
        # ...
    }
    # Matching logic
    return categoria_normalizada
```

**Frequency**: Used in benchmarking and reporting
**Purpose**: Handle variations in user input

### Error Handling Pattern
Services return structured dictionaries with success/error states:

```python
try:
    # Business logic
    return {
        'success': True,
        'predicciones': predicciones,
        'recomendaciones': recomendaciones
    }
except Exception as e:
    return {
        'success': False,
        'error': f'Error en predicción: {str(e)}'
    }
```

**Frequency**: Used in all service methods
**Purpose**: Consistent error handling across the application

## Internal API Usage

### Django ORM Patterns

#### Aggregation with Defaults
Always provide default values for aggregations:
```python
total = Venta.objects.filter(empresa=empresa).aggregate(
    total=Sum('monto')
)['total'] or 0
```

#### Select Related for Performance
Use `select_related` for foreign keys:
```python
ventas = Venta.objects.filter(empresa=empresa).select_related('producto', 'cliente_fk')
```

#### Atomic Transactions
Wrap critical operations in transactions:
```python
from django.db import transaction

with transaction.atomic():
    # Multiple database operations
    venta.save()
    producto.stock -= venta.cantidad
    producto.save()
```

### Custom Middleware Usage

#### Current User Context
Access current user without passing through function parameters:
```python
from empresa.middleware import get_current_user

user = get_current_user()
if user:
    self.creado_por = user
```

### Service Layer Calls

#### Centralized Accounting
Always use `ContabilidadService` for accounting operations:
```python
from empresa.services.contabilidad_service import ContabilidadService

ContabilidadService.crear_asientos_venta(self.empresa, self)
```

#### Gamification Integration
Award XP through `GamificacionService`:
```python
from empresa.services.gamificacion_service import GamificacionService

GamificacionService.otorgar_xp(
    usuario=self.usuario,
    cantidad=50,
    razon="Completó lección de contabilidad"
)
```

### Money Utilities

#### Decimal Conversion
Always convert user input to Decimal:
```python
from empresa.utils.money import to_decimal, quantize_currency

precio = to_decimal(request.POST.get('precio', 0))
total = quantize_currency(precio * cantidad)
```

## Frequently Used Code Idioms

### Safe Dictionary Access
```python
producto = datos_usuario.get('producto', '')
cantidad = int(datos_usuario.get('cantidad', 0))
```

### Conditional Model Creation
```python
cuenta, created = CuentaContable.objects.get_or_create(
    empresa=self.empresa,
    nombre='Caja',
    defaults={'tipo': 'activo'}
)
```

### Bulk Update Pattern
```python
Venta.objects.filter(pk=self.pk).update(cliente_fk=cliente)
```

### JSON Serialization for Decimals
```python
@staticmethod
def _serialize_for_json(obj):
    """Recursively convert Decimals to floats"""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: SimulacionService._serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [SimulacionService._serialize_for_json(v) for v in obj]
    return obj
```

### Trend Calculation (Linear Regression)
```python
def _calcular_tendencia(self, valores):
    """Calcula tendencia lineal usando mínimos cuadrados"""
    n = len(valores)
    x = list(range(n))
    sum_xy = sum(x[i] * valores[i] for i in range(n))
    sum_x2 = sum(xi ** 2 for xi in x)
    pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    return pendiente
```

## Popular Annotations

### Model Meta Options
```python
class Meta:
    unique_together = ('empresa', 'codigo')
    ordering = ['-fecha_creacion']
    indexes = [
        models.Index(fields=['empresa', 'codigo']),
        models.Index(fields=['fecha', 'estado']),
    ]
    verbose_name = 'Cuenta por Cobrar'
    verbose_name_plural = 'Cuentas por Cobrar'
```

### Field Validators
```python
codigo_barras = models.CharField(
    max_length=50,
    blank=True,
    null=True,
    db_index=True,
    help_text="Código de barras para escáner (EAN-13, UPC-A, etc.)"
)
```

### Choice Fields
```python
ESTADO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('completada', 'Completada'),
    ('cancelada', 'Cancelada'),
]

estado = models.CharField(
    max_length=15,
    choices=ESTADO_CHOICES,
    default='pendiente'
)
```

## Testing Patterns

### Test Organization
- Tests organized by feature in `empresa/tests/`
- Naming: `test_[feature].py` (e.g., `test_aprendizaje.py`, `test_simulacion_sandbox.py`)
- Edge cases in separate files: `test_aprendizaje_edgecases.py`

### Test Settings
- Separate settings for testing: `core/test_settings.py` (SQLite)
- CI settings: `core/ci_settings.py` (PostgreSQL)
- Concurrency tests marked for PostgreSQL only

### Common Test Patterns
```python
from django.test import TestCase
from empresa.models import Empresa, Usuario

class VentaTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre="Test Empresa",
            ruc="1234567890001"
        )
        self.usuario = Usuario.objects.create_user(
            username="test",
            empresa=self.empresa
        )
    
    def test_crear_venta(self):
        # Test logic
        self.assertEqual(venta.monto, expected_monto)
```

## Best Practices Summary

1. **Always use Decimal for money**: Never use float for financial calculations
2. **Centralize business logic**: Keep it in service classes, not views or models
3. **Automatic accounting**: Let models create their own accounting entries
4. **Audit everything**: Use `AuditModel` for all transactional models
5. **Sandbox for simulations**: Use transaction savepoints for safe testing
6. **Normalize user input**: Use utility functions for consistency
7. **Return structured responses**: Services return `{'success': bool, ...}` dictionaries
8. **Index foreign keys**: Add database indexes for performance
9. **Provide defaults**: Always handle None/null cases in aggregations
10. **Document NIIF compliance**: Comment accounting standards being followed
