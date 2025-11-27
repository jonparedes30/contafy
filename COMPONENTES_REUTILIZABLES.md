# COMPONENTES REUTILIZABLES - GUÍA DE USO

## 📋 Tabla de Datos (`data_table.html`)

Componente para mostrar datos tabulares con búsqueda y ordenamiento.

### Uso Básico
```django
{% include 'empresa/_components/data_table.html' with items=productos columns=columns title="Productos" %}
```

### Configuración de Columnas
```python
# En la vista:
columns = [
    {'key': 'nombre', 'label': 'Producto', 'sortable': True},
    {'key': 'codigo', 'label': 'Código', 'sortable': True},
    {'key': 'precio_unitario', 'label': 'Precio', 'format': 'currency', 'sortable': True},
    {'key': 'stock', 'label': 'Stock', 'sortable': False},
    {'key': 'fecha_vencimiento', 'label': 'Vencimiento', 'format': 'date'},
]

context = {
    'productos': Producto.objects.filter(empresa=request.user.empresa),
    'columns': columns,
}
```

### Parámetros
- `items`: QuerySet o lista de objetos
- `columns`: Lista de dicts con estructura: `{'key': 'campo', 'label': 'Encabezado', 'sortable': bool, 'format': 'currency|date|boolean'}`
- `title`: Título de la tabla
- `search_placeholder`: Texto de búsqueda (default: "Buscar...")
- `empty_message`: Mensaje sin datos (default: "No hay datos para mostrar")

### Formatos Soportados
- `currency`: Formatea como dinero ($)
- `date`: Formatea como fecha (d/m/Y)
- `boolean`: Muestra Sí/No con badges
- Sin formato: Trunca a 10 palabras

---

## 🔘 Botones de Acción (`action_buttons.html`)

Componente para botones de editar, eliminar, ver.

### Uso Básico
```django
{% include 'empresa/_components/action_buttons.html' with item=producto %}
```

### Con URLs Personalizadas
```django
{% include 'empresa/_components/action_buttons.html' with 
  item=producto 
  edit_url="/empresa/productos/1/editar/" 
  delete_url="/empresa/productos/1/eliminar/"
  show_delete=True
  show_edit=True
%}
```

### Parámetros
- `item`: Objeto con id y opcionalmente `get_edit_url()`, `get_delete_url()`, `get_view_url()`
- `edit_url`: URL para editar (default: `item.get_edit_url()`)
- `delete_url`: URL para eliminar (default: `item.get_delete_url()`)
- `view_url`: URL para ver (default: `item.get_view_url()`)
- `show_edit`: Mostrar botón editar (default: True)
- `show_delete`: Mostrar botón eliminar (default: True)
- `show_view`: Mostrar botón ver (default: False)

### Cómo Implementar en Modelos
```python
class Producto(models.Model):
    # ...
    
    def get_edit_url(self):
        return reverse('empresa:editar_producto', args=[self.id])
    
    def get_delete_url(self):
        return reverse('empresa:eliminar_producto', args=[self.id])
```

---

## 📝 Componentes de Formularios

### Campo de Texto (`forms/text_field.html`)
```django
{% include 'empresa/_components/forms/text_field.html' with 
  field=form.nombre 
  label="Nombre" 
  placeholder="Ingresa el nombre"
%}
```

### Campo Numérico (`forms/number_field.html`)
```django
{% include 'empresa/_components/forms/number_field.html' with 
  field=form.precio 
  label="Precio" 
  step="0.01"
  min="0"
%}
```

### Campo de Fecha (`forms/date_field.html`)
```django
{% include 'empresa/_components/forms/date_field.html' with 
  field=form.fecha_inicio 
  label="Fecha Inicio"
%}
```

### Campo Select (`forms/select_field.html`)
```django
{% include 'empresa/_components/forms/select_field.html' with 
  field=form.categoria 
  label="Categoría"
%}
```

### Campo Textarea (`forms/textarea_field.html`)
```django
{% include 'empresa/_components/forms/textarea_field.html' with 
  field=form.descripcion 
  label="Descripción"
  rows="4"
%}
```

### Parámetros Comunes para Campos
- `field`: Campo del formulario
- `label`: Etiqueta personalizada (default: `field.label`)
- `placeholder`: Placeholder (si aplica)
- Los campos heredan automáticamente:
  - Marcado como requerido si `field.required = True`
  - Validación y mensajes de error
  - Help text

---

## 🎯 Ejemplo Completo

### Template
```django
{% extends 'empresa/base.html' %}

{% block content %}
<div class="container-fluid mt-4">
  <h1>Gestión de Productos</h1>
  
  <!-- Tabla de Productos -->
  {% include 'empresa/_components/data_table.html' with 
    items=productos 
    columns=columns 
    title="Productos"
    search_placeholder="Buscar por nombre o código..."
  %}
  
  <!-- Formulario -->
  <form method="post" class="card mt-4">
    {% csrf_token %}
    <div class="card-header">
      <h5>Crear Producto</h5>
    </div>
    <div class="card-body">
      {% include 'empresa/_components/forms/text_field.html' with field=form.nombre %}
      {% include 'empresa/_components/forms/text_field.html' with field=form.codigo %}
      {% include 'empresa/_components/forms/number_field.html' with field=form.precio_unitario step="0.01" %}
      {% include 'empresa/_components/forms/select_field.html' with field=form.categoria %}
      {% include 'empresa/_components/forms/textarea_field.html' with field=form.descripcion rows="3" %}
    </div>
    <div class="card-footer">
      <button type="submit" class="btn btn-primary">Guardar</button>
      <a href="{% url 'empresa:listar_productos' %}" class="btn btn-secondary">Cancelar</a>
    </div>
  </form>
</div>
{% endblock %}
```

### Vista
```python
def listar_productos(request):
    empresa = request.user.empresa
    productos = Producto.objects.filter(empresa=empresa)
    
    columns = [
        {'key': 'nombre', 'label': 'Producto', 'sortable': True},
        {'key': 'codigo', 'label': 'Código', 'sortable': True},
        {'key': 'precio_unitario', 'label': 'Precio', 'format': 'currency'},
        {'key': 'stock', 'label': 'Stock', 'sortable': True},
    ]
    
    return render(request, 'empresa/productos/listar.html', {
        'productos': productos,
        'columns': columns,
    })
```

---

## ✅ Ventajas

1. **DRY (Don't Repeat Yourself)**: Elimina duplicación en templates
2. **Consistencia Visual**: UI uniforme en toda la app
3. **Mantenimiento Fácil**: Cambios globales en un solo lugar
4. **Accesibilidad**: Componentes siguenpueblos WCAG 2.1
5. **Responsive**: Funcionan en todos los tamaños de pantalla
6. **Bootstrap 5**: Integrados con clases Bootstrap
