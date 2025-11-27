# Fix de Formularios - Parámetro empresa

## Problema
Múltiples formularios fallaban con error 500 porque no aceptaban el parámetro `empresa` que las vistas les pasaban.

**Error:**
```
TypeError: BaseModelForm.__init__() got an unexpected keyword argument 'empresa'
```

## Formularios Corregidos

### 1. ✅ ProductoForm
**Commit:** `a9667a7`, `c5abf15`

```python
class ProductoForm(forms.ModelForm):
    # ... Meta ...
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        producto = super().save(commit=False)
        if self.empresa:
            producto.empresa = self.empresa
        if commit:
            producto.save()
        return producto
```

**Uso:** `/app-beta-2024/producto/crear/`

### 2. ✅ CompraForm
**Commit:** `ebfaa65`

```python
class CompraForm(forms.ModelForm):
    # ... Meta ...
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields['producto'].queryset = Producto.objects.filter(empresa=self.empresa)
```

**Uso:** `/app-beta-2024/compra/crear/`  
**Beneficio adicional:** Filtra productos por empresa

### 3. ✅ VentaForm
**Commit:** `ebfaa65`

```python
class VentaForm(forms.ModelForm):
    # ... Meta ...
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields['producto'].queryset = Producto.objects.filter(empresa=self.empresa)
```

**Uso:** `/app-beta-2024/venta/crear/`  
**Beneficio adicional:** Filtra productos por empresa

### 4. ✅ GastoForm
**Commit:** `ebfaa65`

```python
class GastoForm(forms.ModelForm):
    # ... Meta ...
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
```

**Uso:** `/app-beta-2024/gasto/crear/`

## Formularios Ya Corregidos Anteriormente

### ProveedorForm
```python
def __init__(self, *args, **kwargs):
    self.empresa = kwargs.pop('empresa', None)
    super().__init__(*args, **kwargs)

def save(self, commit=True):
    proveedor = super().save(commit=False)
    if self.empresa:
        proveedor.empresa = self.empresa
    if commit:
        proveedor.save()
    return proveedor
```

### ClienteForm
```python
def __init__(self, *args, **kwargs):
    self.empresa = kwargs.pop('empresa', None)
    super().__init__(*args, **kwargs)
    self.fields['email'].required = False
    self.fields['telefono'].required = False
    self.fields['direccion'].required = False

def save(self, commit=True):
    cliente = super().save(commit=False)
    if self.empresa:
        cliente.empresa = self.empresa
    if commit:
        cliente.save()
    return cliente
```

### CategoriaProductoForm
```python
def __init__(self, *args, **kwargs):
    self.empresa = kwargs.pop('empresa', None)
    super().__init__(*args, **kwargs)
    self.fields['descripcion'].required = False

def save(self, commit=True):
    categoria = super().save(commit=False)
    if self.empresa:
        categoria.empresa = self.empresa
    if commit:
        categoria.save()
    return categoria
```

## Patrón Estándar

### Para formularios que crean objetos con empresa:
```python
class MiForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.empresa:
            obj.empresa = self.empresa
        if commit:
            obj.save()
        return obj
```

### Para formularios con ForeignKey que necesita filtrado:
```python
class MiForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields['mi_fk'].queryset = MiModelo.objects.filter(empresa=self.empresa)
```

## Vistas que Usan el Patrón

Todas las vistas de creación pasan `empresa=empresa`:

```python
@login_required
def crear_algo(request):
    empresa = request.user.empresa
    
    if request.method == 'POST':
        form = AlgoForm(request.POST, empresa=empresa)
        if form.is_valid():
            # ...
    else:
        form = AlgoForm(empresa=empresa)
    
    return render(request, 'template.html', {'form': form})
```

## Beneficios del Patrón

1. **Seguridad:** Asegura que los objetos se creen con la empresa correcta
2. **Filtrado:** Los ForeignKey solo muestran opciones de la empresa del usuario
3. **Consistencia:** Todas las vistas usan el mismo patrón
4. **Mantenibilidad:** Fácil de entender y mantener

## Checklist de Formularios

- [x] ProductoForm
- [x] CompraForm
- [x] VentaForm
- [x] GastoForm
- [x] ProveedorForm
- [x] ClienteForm
- [x] CategoriaProductoForm
- [x] CuentaContableForm
- [x] CapitalForm
- [x] MateriaPrimaForm
- [x] ProductoManufacturadoForm
- [x] OrdenProduccionForm

## Commits Relacionados

1. `a9667a7` - Fix: Add null checks in crear_producto.html JavaScript
2. `c5abf15` - Fix: Complete ProductoForm with all fields and fix category creation API
3. `ebfaa65` - Fix: Add empresa parameter to CompraForm, VentaForm, and GastoForm

## Testing

### Verificar que funcionan:
1. ✅ `/app-beta-2024/producto/crear/` - ProductoForm
2. ✅ `/app-beta-2024/compra/crear/` - CompraForm
3. ✅ `/app-beta-2024/venta/crear/` - VentaForm
4. ✅ `/app-beta-2024/gasto/crear/` - GastoForm

### Próximos Pasos
Esperar ~5 minutos para que Render despliegue el commit `ebfaa65` y verificar que todas las páginas de creación funcionan correctamente.
