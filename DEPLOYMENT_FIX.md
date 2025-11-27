# Fix para Error 500 en /app-beta-2024/producto/crear/

## Problema
Error: `BaseModelForm.__init__() got an unexpected keyword argument 'empresa'`

## Causa
El servidor de producción (Render) está usando código en caché antiguo donde `ProductoForm` no tenía el método `__init__` que acepta el parámetro `empresa`.

## Solución Verificada
El código ya está corregido en el repositorio:
- `ProductoForm` en `empresa/forms.py` tiene el método `__init__` correcto (líneas 343-345)
- `ProductoForm` tiene el método `save` correcto (líneas 347-354)
- Todas las vistas usan `ProductoForm(empresa=empresa)` correctamente

## Pasos para Desplegar el Fix

### Opción 1: Redesplegar en Render (Recomendado)
1. Ir al dashboard de Render: https://dashboard.render.com
2. Seleccionar el servicio "contafy"
3. Hacer clic en "Manual Deploy" > "Deploy latest commit"
4. Esperar a que termine el despliegue (~5-10 minutos)

### Opción 2: Forzar Actualización con Git
```bash
# Hacer un commit vacío para forzar redespliegue
git commit --allow-empty -m "Force redeploy: Fix ProductoForm __init__ method"
git push origin main
```

### Opción 3: Limpiar Cache de Python en Render
Si Render tiene acceso a shell:
```bash
# Eliminar archivos .pyc
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete

# Reiniciar el servicio
# (Render lo hace automáticamente al redesplegar)
```

## Verificación Post-Despliegue
1. Ir a: https://contafy.onrender.com/app-beta-2024/producto/crear/
2. Verificar que la página carga sin error 500
3. Intentar crear un producto de prueba

## Código Corregido (Ya en el Repo)

### empresa/forms.py (líneas 338-354)
```python
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'precio_unitario', 'stock']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
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

### empresa/views/productos.py (líneas 18-19, 56)
```python
# Crear producto
form = ProductoForm(request.POST, empresa=empresa)

# Editar producto  
form = ProductoForm(empresa=empresa, instance=producto)
```

## Notas
- El error solo ocurre en producción porque el servidor tiene código en caché
- El código local funciona correctamente (verificado con `verificar_productoform.py`)
- Este es un problema de despliegue, no de código
