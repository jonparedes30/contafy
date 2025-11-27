# Fix CompraForm - Campo Proveedor

## Problema Identificado
1. El campo **proveedor** no aparecía en el formulario de compras
2. El **precio de costo** no se mostraba (campo `monto`)

## Solución Aplicada

### CompraForm Actualizado

**Antes:**
```python
class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['producto', 'cantidad', 'monto', 'tipo_pago']
```

**Después:**
```python
class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['proveedor_fk', 'producto', 'cantidad', 'monto', 'tipo_pago']
        widgets = {
            'proveedor_fk': forms.Select(attrs={'class': 'form-select'}),
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_pago': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'proveedor_fk': 'Proveedor',
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields['producto'].queryset = Producto.objects.filter(empresa=self.empresa)
            from empresa.models import Proveedor
            self.fields['proveedor_fk'].queryset = Proveedor.objects.filter(
                empresa=self.empresa, 
                activo=True
            )
        self.fields['proveedor_fk'].required = False
```

## Cambios Realizados

### 1. ✅ Campo Proveedor Agregado
- Campo: `proveedor_fk`
- Tipo: ForeignKey a modelo Proveedor
- Widget: Select con clase Bootstrap
- Label: "Proveedor"
- Requerido: No (opcional)
- Filtrado: Solo proveedores activos de la empresa

### 2. ✅ Campo Monto (Precio de Costo)
- Ya estaba en el formulario
- Widget: NumberInput con step 0.01
- Clase: form-control
- Este campo representa el **precio total de la compra** (cantidad × precio unitario)

## Modelo Compra

El modelo Compra tiene los siguientes campos relacionados:

```python
class Compra(AuditModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    proveedor_fk = models.ForeignKey(
        'empresa.Proveedor', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='compras',
        help_text="Proveedor registrado (opcional)"
    )
    proveedor_nombre = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Nombre del proveedor (si no está registrado)"
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    monto_neto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tasa_iva = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    tipo_pago = models.CharField(max_length=10, choices=TIPO_PAGO_CHOICES)
```

## Campos del Formulario de Compra

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| **Proveedor** | Select | No | Proveedor de la compra (opcional) |
| **Producto** | Select | Sí | Producto a comprar |
| **Cantidad** | Number | Sí | Cantidad de unidades |
| **Monto** | Number | Sí | Precio total (con IVA) |
| **Tipo de Pago** | Select | Sí | Contado o Crédito |

## Cálculo Automático de IVA

El modelo Compra calcula automáticamente:
- `monto_neto` = monto / (1 + tasa_iva/100)
- `iva` = monto - monto_neto

## Funcionalidades

### 1. Selección de Proveedor
- Lista desplegable con proveedores activos
- Filtrado por empresa del usuario
- Campo opcional (puede dejarse vacío)

### 2. Selección de Producto
- Lista desplegable con productos de la empresa
- Filtrado por empresa del usuario

### 3. Cálculo de Precio
- Campo `monto` es el precio total de la compra
- El sistema calcula automáticamente el IVA
- Actualiza el stock del producto

### 4. Tipo de Pago
- **Contado**: Descuenta de Caja inmediatamente
- **Crédito**: Crea cuenta por pagar

## Nota sobre ProductoForm

El modelo `Producto` **NO tiene** campo `proveedor_principal`. 

Si se desea agregar esta funcionalidad en el futuro, se necesitaría:

1. Crear migración para agregar campo al modelo:
```python
proveedor_principal = models.ForeignKey(
    'Proveedor',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='productos_principales'
)
```

2. Actualizar ProductoForm para incluir el campo

Por ahora, la relación producto-proveedor se maneja a través de las compras.

## Commit

**Commit:** `88c42d1` - Fix: Add proveedor_fk field to CompraForm

## Testing

### Verificar que funciona:
1. ✅ Ir a `/app-beta-2024/compra/crear/`
2. ✅ Ver campo "Proveedor" en el formulario
3. ✅ Ver campo "Monto" (precio de costo)
4. ✅ Seleccionar proveedor de la lista
5. ✅ Crear compra y verificar que se guarda el proveedor
6. ✅ Verificar que el stock del producto se actualiza

## Próximos Pasos

Esperar ~5 minutos para que Render despliegue el commit `88c42d1` y verificar que:
1. El campo proveedor aparece en el formulario
2. Se puede seleccionar un proveedor
3. El proveedor se guarda correctamente
4. El campo monto funciona correctamente
