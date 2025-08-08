# Solución: Gestión de Proveedores para Materias Primas

## Problema Identificado
En el módulo de materias primas no se podía añadir el nombre o los datos del proveedor porque:
1. No existía una interfaz completa para gestionar proveedores
2. El campo `proveedor_principal` aparecía vacío si no había proveedores creados
3. No había forma fácil de crear proveedores desde la interfaz de materias primas

## Solución Implementada

### 1. Formulario de Proveedor
- **Archivo**: `empresa/forms.py`
- **Cambio**: Agregado `ProveedorForm` con todos los campos necesarios
- **Campos incluidos**: nombre, ruc, teléfono, email, dirección, días_credito

### 2. Vista AJAX para Crear Proveedores
- **Archivo**: `empresa/views/manufactura.py`
- **Función**: `crear_proveedor_ajax()`
- **Funcionalidad**: Permite crear proveedores desde modales sin recargar la página

### 3. URL para la Nueva Vista
- **Archivo**: `empresa/urls.py`
- **Ruta agregada**: `manufactura/proveedores/crear-ajax/`

### 4. Templates Actualizados

#### Template de Crear Materia Prima
- **Archivo**: `empresa/templates/empresa/manufactura/crear_materia_prima.html`
- **Cambios**:
  - Botón "Nuevo" junto al campo de proveedor
  - Modal completo para crear proveedores
  - JavaScript para manejar la creación AJAX
  - Actualización automática del select de proveedores

#### Template de Listar Materias Primas
- **Archivo**: `empresa/templates/empresa/manufactura/listar_materias_primas.html`
- **Cambios**:
  - Botón "Nuevo Proveedor" en la barra superior
  - Modal para crear proveedores
  - JavaScript para manejar la creación

### 5. Nueva Página de Gestión de Proveedores
- **Vista**: `listar_proveedores()` en `empresa/views/manufactura.py`
- **Template**: `empresa/templates/empresa/manufactura/listar_proveedores.html`
- **URL**: `manufactura/proveedores/`
- **Funcionalidad**: Lista completa de proveedores con opción de crear nuevos

### 6. Menú de Navegación Actualizado
- **Archivo**: `empresa/templates/empresa/base.html`
- **Cambio**: Agregado enlace "Proveedores" en el menú de Materias Primas

### 7. Comando de Gestión
- **Archivo**: `empresa/management/commands/crear_proveedores_default.py`
- **Propósito**: Crear proveedores por defecto para empresas existentes

## Cómo Usar la Solución

### Para Crear un Proveedor:

#### Opción 1: Desde Materias Primas
1. Ir a "Materias Primas" → "Ver Materias Primas" o "Nueva Materia Prima"
2. Hacer clic en el botón "Nuevo Proveedor"
3. Llenar el formulario en el modal
4. Guardar

#### Opción 2: Desde Gestión de Proveedores
1. Ir a "Materias Primas" → "Proveedores"
2. Hacer clic en "Nuevo Proveedor"
3. Llenar el formulario en el modal
4. Guardar

### Para Asignar Proveedor a Materia Prima:
1. Al crear o editar una materia prima
2. Seleccionar el proveedor del dropdown "Proveedor Principal"
3. Si no existe el proveedor, usar el botón "Nuevo" para crearlo

## Comandos de Instalación

```bash
# Ejecutar migraciones (si es necesario)
python manage.py makemigrations
python manage.py migrate

# Crear proveedores por defecto para empresas existentes
python manage.py crear_proveedores_default
```

## Características de la Solución

### ✅ Funcionalidades Implementadas:
- ✅ Crear proveedores desde modales AJAX
- ✅ Listar y gestionar proveedores
- ✅ Asignar proveedores a materias primas
- ✅ Interfaz integrada en el flujo de trabajo
- ✅ Validación de formularios
- ✅ Navegación intuitiva

### 🔄 Funcionalidades Futuras (Opcionales):
- Editar proveedores existentes
- Eliminar proveedores (con validaciones)
- Importar proveedores desde Excel
- Historial de compras por proveedor
- Evaluación de proveedores

## Archivos Modificados

1. `empresa/forms.py` - Agregado ProveedorForm
2. `empresa/views/manufactura.py` - Agregadas vistas de proveedores
3. `empresa/urls.py` - Agregadas URLs de proveedores
4. `empresa/templates/empresa/manufactura/crear_materia_prima.html` - Modal y botón
5. `empresa/templates/empresa/manufactura/listar_materias_primas.html` - Modal y botón
6. `empresa/templates/empresa/base.html` - Enlace en menú
7. `empresa/templates/empresa/manufactura/listar_proveedores.html` - Nuevo template
8. `empresa/management/commands/crear_proveedores_default.py` - Nuevo comando

## Resultado Final

Ahora los usuarios pueden:
1. **Ver** todos sus proveedores en una lista organizada
2. **Crear** nuevos proveedores fácilmente desde múltiples lugares
3. **Asignar** proveedores a materias primas sin problemas
4. **Gestionar** la información completa de cada proveedor

El problema original está completamente resuelto con una solución integral y fácil de usar.