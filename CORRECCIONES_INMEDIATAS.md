# CORRECCIONES INMEDIATAS - CONTAFY
## Código Listo para Copiar y Pegar

Este documento contiene las correcciones exactas que puedes aplicar inmediatamente.

---

## CORRECCIÓN 1: Proteger Endpoints de Debug

### Archivo: `empresa/urls.py`

**Buscar (alrededor de línea 157-158):**
```python
# URLs de prueba para filtros
path('test/filtros/', test_filtros_fecha, name='test_filtros_fecha'),
path('test/verificar-fecha/', verificar_datos_fecha, name='verificar_datos_fecha'),
```

**Reemplazar con:**
```python
# URLs de prueba para filtros (solo en DEBUG)
if settings.DEBUG:
    urlpatterns += [
        path('test/filtros/', test_filtros_fecha, name='test_filtros_fecha'),
        path('test/verificar-fecha/', verificar_datos_fecha, name='verificar_datos_fecha'),
    ]
```

**Buscar (alrededor de línea 280):**
```python
# URL de debug
path('debug/datos/', lambda request: __import__('empresa.views.debug_datos', fromlist=['debug_datos']).debug_datos(request), name='debug_datos'),
```

**Reemplazar con:**
```python
# URL de debug (solo en DEBUG)
if settings.DEBUG:
    urlpatterns += [
        path('debug/datos/', lambda request: __import__('empresa.views.debug_datos', fromlist=['debug_datos']).debug_datos(request), name='debug_datos'),
    ]
```

---

## CORRECCIÓN 2: Remover Menú de Manufactura (Temporal)

### Archivo: `empresa/templates/empresa/base.html`

**Buscar (línea 360-440):**
```html
<!-- MANUFACTURA (Solo para empresas de manufactura) -->
{% if user.empresa.categoria == 'manufactura' %}
  {% if is_owner or user_powers.puede_gestionar_inventario %}
  <li class="nav-item">
    <a class="nav-link" data-bs-toggle="collapse" href="#materiasMenu">
      <i class="bi bi-boxes me-2"></i>Materias Primas <i class="bi bi-chevron-down ms-auto"></i>
    </a>
    <div class="collapse" id="materiasMenu">
      <ul class="nav flex-column ms-3">
        <!-- Enlaces comentados -->
      </ul>
    </div>
  </li>
  {% endif %}
  <!-- ... más secciones ... -->
{% endif %}
```

**Reemplazar con:**
```html
<!-- MANUFACTURA (Solo para empresas de manufactura) -->
<!-- TEMPORALMENTE DESHABILITADO - En desarrollo -->
{% if user.empresa.categoria == 'manufactura' and False %}
  {% if is_owner or user_powers.puede_gestionar_inventario %}
  <li class="nav-item">
    <a class="nav-link" data-bs-toggle="collapse" href="#materiasMenu">
      <i class="bi bi-boxes me-2"></i>Materias Primas <i class="bi bi-chevron-down ms-auto"></i>
    </a>
    <div class="collapse" id="materiasMenu">
      <ul class="nav flex-column ms-3">
        <!-- Enlaces comentados -->
      </ul>
    </div>
  </li>
  {% endif %}
  <!-- ... más secciones ... -->
{% endif %}

<!-- MENSAJE TEMPORAL PARA USUARIOS DE MANUFACTURA -->
{% if user.empresa.categoria == 'manufactura' %}
<li class="nav-item">
  <div class="alert alert-info mx-3 mt-2" role="alert" style="font-size: 0.85rem;">
    <i class="bi bi-info-circle me-1"></i>
    <strong>Módulo de Manufactura:</strong> Próximamente disponible.
  </div>
</li>
{% endif %}
```

---

## CORRECCIÓN 3: Agregar Validación en Simulaciones

### Archivo: `empresa/api/views.py`

**Buscar (línea 120):**
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulacion_finalizar(request, simulacion_id):
    """Finaliza y procesa una simulación"""
    simulacion = get_object_or_404(
        SimulacionUsuario, 
        id=simulacion_id, 
        usuario=request.user
    )
    
    serializer = SimulacionGuardarSerializer(data=request.data)
```

**Reemplazar con:**
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulacion_finalizar(request, simulacion_id):
    """Finaliza y procesa una simulación"""
    simulacion = get_object_or_404(
        SimulacionUsuario, 
        id=simulacion_id, 
        usuario=request.user
    )
    
    # Validar que no esté ya completada
    if simulacion.completada:
        return Response(
            {
                'error': 'Esta simulación ya fue completada',
                'simulacion_id': simulacion_id,
                'completada_en': simulacion.completada_en
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = SimulacionGuardarSerializer(data=request.data)
```

---

## CORRECCIÓN 4: Implementar Paginación Básica

### Archivo: `empresa/api/views.py`

**Agregar al inicio del archivo (después de los imports):**
```python
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

**Buscar (línea 19):**
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def modulos_list(request):
    """Lista módulos filtrados por tipo de empresa del usuario"""
    tipo_empresa = request.GET.get('tipo_empresa', 'comercial')
    
    modulos = ModuloAprendizaje.objects.filter(
        tipo_empresa=tipo_empresa,
        visible=True,
        activo=True
    ).order_by('orden')
    
    serializer = ModuloAprendizajeSerializer(modulos, many=True)
    return Response(serializer.data)
```

**Reemplazar con:**
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def modulos_list(request):
    """Lista módulos filtrados por tipo de empresa del usuario"""
    tipo_empresa = request.GET.get('tipo_empresa', 'comercial')
    
    modulos = ModuloAprendizaje.objects.filter(
        tipo_empresa=tipo_empresa,
        visible=True,
        activo=True
    ).order_by('orden')
    
    # Aplicar paginación
    paginator = StandardPagination()
    page = paginator.paginate_queryset(modulos, request)
    if page is not None:
        serializer = ModuloAprendizajeSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    # Fallback sin paginación (para compatibilidad)
    serializer = ModuloAprendizajeSerializer(modulos, many=True)
    return Response(serializer.data)
```

**Aplicar el mismo patrón a:**
- `lecciones_list()` (línea 32)
- `escenarios_list()` (línea 195)

---

## CORRECCIÓN 5: Refactorizar Importaciones Lambda

### Archivo: `empresa/urls.py`

**Agregar al inicio del archivo (después de las importaciones existentes):**
```python
# Importaciones para vistas que estaban con lambda
from empresa.views.valuacion import valuacion_empresa
from empresa.views.responder_solicitud import responder_solicitud_web
from empresa.views.aprendizaje_views import (
    leccion_interactiva, 
    marcar_leccion_completada,
    marcar_paso_completado, 
    modulo_detalle as modulo_detalle_ux, 
    perfil_aprendizaje
)
from empresa.views.ai_reports import vista_reporte_ia, generar_reporte_ia_pdf
from empresa.views.ai_comandos import (
    AIComandosView, 
    procesar_comando_rapido,
    ayuda_comandos, 
    ejemplos_comandos
)
from empresa.views.debug_datos import debug_datos
from django.shortcuts import render
```

**Buscar y reemplazar:**

**1. Valuación (línea ~234):**
```python
# ANTES:
path('valuacion/', lambda request: __import__('empresa.views.valuacion', fromlist=['valuacion_empresa']).valuacion_empresa(request), name='valuacion_empresa'),

# DESPUÉS:
path('valuacion/', valuacion_empresa, name='valuacion_empresa'),
```

**2. Responder Solicitud (línea ~237):**
```python
# ANTES:
path('responder/<int:solicitud_id>/', lambda request, solicitud_id: __import__('empresa.views.responder_solicitud', fromlist=['responder_solicitud_web']).responder_solicitud_web(request, solicitud_id), name='responder_solicitud_web'),

# DESPUÉS:
path('responder/<int:solicitud_id>/', responder_solicitud_web, name='responder_solicitud_web'),
```

**3. Academia UX (líneas ~247-250):**
```python
# ANTES:
path('aprendizaje/leccion/<int:leccion_id>/interactiva/', lambda request, leccion_id: __import__('empresa.views.aprendizaje_views', fromlist=['leccion_interactiva']).leccion_interactiva(request, leccion_id), name='leccion_interactiva'),
path('aprendizaje/leccion/<int:leccion_id>/completar/', lambda request, leccion_id: __import__('empresa.views.aprendizaje_views', fromlist=['marcar_leccion_completada']).marcar_leccion_completada(request, leccion_id), name='marcar_leccion_completada'),
path('aprendizaje/leccion/<int:leccion_id>/paso/<int:paso_index>/completar/', lambda request, leccion_id, paso_index: __import__('empresa.views.aprendizaje_views', fromlist=['marcar_paso_completado']).marcar_paso_completado(request, leccion_id, paso_index), name='marcar_paso_completado'),
path('aprendizaje/modulo/<int:modulo_id>/detalle/', lambda request, modulo_id: __import__('empresa.views.aprendizaje_views', fromlist=['modulo_detalle']).modulo_detalle(request, modulo_id), name='modulo_detalle_ux'),
path('aprendizaje/perfil-ux/', lambda request: __import__('empresa.views.aprendizaje_views', fromlist=['perfil_aprendizaje']).perfil_aprendizaje(request), name='perfil_aprendizaje_ux'),

# DESPUÉS:
path('aprendizaje/leccion/<int:leccion_id>/interactiva/', leccion_interactiva, name='leccion_interactiva'),
path('aprendizaje/leccion/<int:leccion_id>/completar/', marcar_leccion_completada, name='marcar_leccion_completada'),
path('aprendizaje/leccion/<int:leccion_id>/paso/<int:paso_index>/completar/', marcar_paso_completado, name='marcar_paso_completado'),
path('aprendizaje/modulo/<int:modulo_id>/detalle/', modulo_detalle_ux, name='modulo_detalle_ux'),
path('aprendizaje/perfil-ux/', perfil_aprendizaje, name='perfil_aprendizaje_ux'),
```

**4. Reportes IA (líneas ~268-269):**
```python
# ANTES:
path('reporte-ia/', lambda request: __import__('empresa.views.ai_reports', fromlist=['vista_reporte_ia']).vista_reporte_ia(request), name='vista_reporte_ia'),
path('reporte-ia/pdf/', lambda request: __import__('empresa.views.ai_reports', fromlist=['generar_reporte_ia_pdf']).generar_reporte_ia_pdf(request), name='generar_reporte_ia_pdf'),

# DESPUÉS:
path('reporte-ia/', vista_reporte_ia, name='vista_reporte_ia'),
path('reporte-ia/pdf/', generar_reporte_ia_pdf, name='generar_reporte_ia_pdf'),
```

**5. Comandos IA (líneas ~271-276):**
```python
# ANTES:
path('ai-comandos/', lambda request: __import__('django.shortcuts', fromlist=['render']).render(request, 'empresa/ai_comandos.html'), name='ai_comandos_page'),
path('api/ai-comandos/', lambda request: __import__('empresa.views.ai_comandos', fromlist=['AIComandosView']).AIComandosView.as_view()(request), name='ai_comandos'),
path('api/comando-rapido/', lambda request: __import__('empresa.views.ai_comandos', fromlist=['procesar_comando_rapido']).procesar_comando_rapido(request), name='comando_rapido'),
path('api/ayuda-comandos/', lambda request: __import__('empresa.views.ai_comandos', fromlist=['ayuda_comandos']).ayuda_comandos(request), name='ayuda_comandos'),
path('api/ejemplos-comandos/', lambda request: __import__('empresa.views.ai_comandos', fromlist=['ejemplos_comandos']).ejemplos_comandos(request), name='ejemplos_comandos'),

# DESPUÉS:
path('ai-comandos/', lambda request: render(request, 'empresa/ai_comandos.html'), name='ai_comandos_page'),
path('api/ai-comandos/', AIComandosView.as_view(), name='ai_comandos'),
path('api/comando-rapido/', procesar_comando_rapido, name='comando_rapido'),
path('api/ayuda-comandos/', ayuda_comandos, name='ayuda_comandos'),
path('api/ejemplos-comandos/', ejemplos_comandos, name='ejemplos_comandos'),
```

---

## CORRECCIÓN 6: Resolver Duplicación de URL

### Archivo: `empresa/urls.py`

**Buscar (líneas 95-96):**
```python
path('venta/<int:venta_id>/editar/', editar_venta, name='editar_venta'),
path('venta/<int:venta_id>/eliminar/', eliminar_venta, name='eliminar_venta'),
path('api/venta/<int:venta_id>/eliminar/', eliminar_venta, name='api_eliminar_venta'),
```

**Reemplazar con:**
```python
path('venta/<int:venta_id>/editar/', editar_venta, name='editar_venta'),
path('venta/<int:venta_id>/eliminar/', eliminar_venta, name='eliminar_venta'),
# Nota: Usar 'eliminar_venta' para ambos casos (web y API)
```

**Actualizar en templates que usen 'api_eliminar_venta':**
```javascript
// Buscar en archivos .html y .js:
// ANTES:
url: "{% url 'empresa:api_eliminar_venta' venta.id %}"

// DESPUÉS:
url: "{% url 'empresa:eliminar_venta' venta.id %}"
```

---

## CORRECCIÓN 7: Mejorar CSRF en APIs

### Archivo: `empresa/views/empresa.py`

**Buscar (línea 73):**
```python
@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def gestion_poderes_empleado(request, empresa_id, empleado_id):
```

**Reemplazar con:**
```python
@login_required
@require_http_methods(["GET", "POST"])
def gestion_poderes_empleado(request, empresa_id, empleado_id):
```

**Buscar (línea 145):**
```python
@csrf_exempt
@login_required
@require_owner
@require_http_methods(["POST"])
def eliminar_empleado(request, empleado_id):
```

**Reemplazar con:**
```python
@login_required
@require_owner
@require_http_methods(["POST"])
def eliminar_empleado(request, empleado_id):
```

**Buscar (línea 159):**
```python
@csrf_exempt
@login_required
@require_owner
@require_http_methods(["POST"])
def editar_empresa(request):
```

**Reemplazar con:**
```python
@login_required
@require_owner
@require_http_methods(["POST"])
def editar_empresa(request):
```

**Buscar (línea 169):**
```python
@csrf_exempt
@login_required
@require_http_methods(["POST"])
def editar_usuario(request):
```

**Reemplazar con:**
```python
@login_required
@require_http_methods(["POST"])
def editar_usuario(request):
```

**IMPORTANTE:** Después de estos cambios, asegúrate de que el frontend envíe el token CSRF:

```javascript
// En archivos JavaScript que hacen POST
fetch(url, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')  // Función para obtener el token
    },
    body: JSON.stringify(data)
});

// Función helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

---

## VERIFICACIÓN POST-CORRECCIONES

### 1. Ejecutar Tests
```bash
python manage.py test empresa.tests
```

### 2. Verificar URLs
```bash
python manage.py show_urls | grep -E "(test|debug|manufactura)"
```

### 3. Verificar Imports
```bash
python manage.py check
```

### 4. Probar Manualmente
- [ ] Login y logout
- [ ] Crear venta
- [ ] Eliminar venta
- [ ] Acceder a reportes
- [ ] Probar simulaciones
- [ ] Verificar que debug URLs no sean accesibles en producción

---

## CHECKLIST DE APLICACIÓN

- [ ] Corrección 1: Proteger endpoints de debug
- [ ] Corrección 2: Remover menú de manufactura
- [ ] Corrección 3: Validación en simulaciones
- [ ] Corrección 4: Paginación en APIs
- [ ] Corrección 5: Refactorizar lambdas
- [ ] Corrección 6: Resolver duplicación URL
- [ ] Corrección 7: Mejorar CSRF
- [ ] Ejecutar tests
- [ ] Verificar en desarrollo
- [ ] Commit y push
- [ ] Deploy a staging
- [ ] Verificar en staging
- [ ] Deploy a producción

---

## NOTAS IMPORTANTES

1. **Backup antes de aplicar:** Haz backup de la base de datos antes de aplicar cambios
2. **Aplicar en orden:** Las correcciones están ordenadas por prioridad
3. **Testing:** Ejecuta tests después de cada corrección
4. **Rollback plan:** Ten un plan de rollback por si algo falla

---

**Última actualización:** 2025
**Aplicar en:** Desarrollo → Staging → Producción
