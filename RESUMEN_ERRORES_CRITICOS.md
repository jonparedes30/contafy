# 🔴 ERRORES CRÍTICOS - CONTAFY
## Resumen Ejecutivo de Problemas que Requieren Acción Inmediata

---

## 1. FUNCIONALIDAD DE MANUFACTURA ROTA ❌

### Problema
Las URLs de manufactura están comentadas pero el menú las muestra, causando enlaces rotos.

### Archivos Afectados
- `empresa/urls.py` (líneas 186-203)
- `empresa/templates/empresa/base.html` (líneas 367-436)

### URLs Rotas (15 enlaces)
```
/manufactura/materias-primas/
/manufactura/materias-primas/crear/
/manufactura/materias-primas/<id>/editar/
/manufactura/proveedores/
/manufactura/proveedores/crear-ajax/
/manufactura/productos/
/manufactura/productos/crear/
/manufactura/productos/<id>/editar/
/manufactura/ordenes/
/manufactura/ordenes/crear/
/manufactura/ordenes/<id>/
/manufactura/ordenes/<id>/iniciar/
/manufactura/ordenes/<id>/completar/
/manufactura/productos/<id>/cambiar-estado/
/manufactura/
```

### Impacto
- ❌ Usuarios con empresas tipo "manufactura" ven menús vacíos
- ❌ Clicks en enlaces generan error 404
- ❌ Experiencia de usuario completamente rota para este tipo de empresa

### Solución Inmediata
**Opción A - Habilitar (si las vistas existen):**
```python
# En empresa/urls.py, descomentar líneas 186-203
# En base.html, descomentar líneas 367-436
```

**Opción B - Remover del menú (recomendado si no está listo):**
```html
<!-- En base.html, eliminar o condicionar secciones de manufactura -->
{% if user.empresa.categoria == 'manufactura' and MANUFACTURA_ENABLED %}
```

---

## 2. ENDPOINTS DE DEBUG EXPUESTOS 🔓

### Problema
Endpoints de testing y debug accesibles sin autenticación de admin.

### URLs Expuestas
```
/app-beta-2024/test/filtros/
/app-beta-2024/test/verificar-fecha/
/app-beta-2024/debug/datos/
```

### Riesgo
- 🔓 Exposición de información sensible del sistema
- 🔓 Posible manipulación de datos en producción
- 🔓 Information disclosure

### Solución Inmediata
```python
# En empresa/urls.py
from django.contrib.admin.views.decorators import staff_member_required

path('test/filtros/', staff_member_required(test_filtros_fecha), name='test_filtros_fecha'),
path('test/verificar-fecha/', staff_member_required(verificar_datos_fecha), name='verificar_datos_fecha'),
path('debug/datos/', staff_member_required(debug_datos), name='debug_datos'),
```

O mejor aún, usar settings:
```python
if settings.DEBUG:
    urlpatterns += [
        path('test/filtros/', test_filtros_fecha, name='test_filtros_fecha'),
        path('debug/datos/', debug_datos, name='debug_datos'),
    ]
```

---

## 3. CSRF EXEMPT EN APIS INTERNAS ⚠️

### Problema
Varias vistas usan `@csrf_exempt` sin justificación clara.

### Archivos Afectados
`empresa/views/empresa.py`:
- Línea 73: `gestion_poderes_empleado`
- Línea 145: `eliminar_empleado`
- Línea 159: `editar_empresa`
- Línea 169: `editar_usuario`

### Riesgo
- ⚠️ Vulnerabilidad CSRF
- ⚠️ Posible manipulación de datos por atacantes

### Solución
**Opción A - Usar CSRF Token:**
```python
# Remover @csrf_exempt
# Asegurar que el frontend envíe el token CSRF
```

**Opción B - Migrar a API REST con JWT:**
```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def editar_empresa(request):
    # JWT maneja la autenticación
```

---

## 4. FALTA DE PAGINACIÓN EN APIS 📊

### Problema
APIs retornan todos los registros sin límite.

### APIs Afectadas
```python
# empresa/api/views.py
modulos_list()        # Línea 19
lecciones_list()      # Línea 32
escenarios_list()     # Línea 195
```

### Impacto
- 📊 Lentitud con muchos registros
- 📊 Consumo excesivo de memoria
- 📊 Timeout en requests

### Solución
```python
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def modulos_list(request):
    tipo_empresa = request.GET.get('tipo_empresa', 'comercial')
    modulos = ModuloAprendizaje.objects.filter(
        tipo_empresa=tipo_empresa,
        visible=True,
        activo=True
    ).order_by('orden')
    
    paginator = StandardPagination()
    page = paginator.paginate_queryset(modulos, request)
    serializer = ModuloAprendizajeSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)
```

---

## 5. IMPORTACIONES CON LAMBDA 🔧

### Problema
Uso de `lambda` con `__import__` dificulta debugging y testing.

### Ejemplos en empresa/urls.py
```python
# Línea 234
path('valuacion/', lambda request: __import__('empresa.views.valuacion', fromlist=['valuacion_empresa']).valuacion_empresa(request), name='valuacion_empresa'),

# Línea 237
path('responder/<int:solicitud_id>/', lambda request, solicitud_id: __import__('empresa.views.responder_solicitud', fromlist=['responder_solicitud_web']).responder_solicitud_web(request, solicitud_id), name='responder_solicitud_web'),

# Líneas 247-250 (Academia UX)
# Líneas 268-269 (Reportes IA)
# Líneas 271-276 (Comandos IA)
```

### Problemas
- 🔧 Stack traces confusos
- 🔧 Imposible hacer mocking en tests
- 🔧 IDEs no pueden navegar al código
- 🔧 Dificulta refactoring

### Solución
```python
# Al inicio del archivo
from empresa.views.valuacion import valuacion_empresa
from empresa.views.responder_solicitud import responder_solicitud_web
from empresa.views.aprendizaje_views import (
    leccion_interactiva, marcar_leccion_completada,
    marcar_paso_completado, modulo_detalle, perfil_aprendizaje
)
from empresa.views.ai_reports import vista_reporte_ia, generar_reporte_ia_pdf
from empresa.views.ai_comandos import (
    AIComandosView, procesar_comando_rapido,
    ayuda_comandos, ejemplos_comandos
)

# En urlpatterns
path('valuacion/', valuacion_empresa, name='valuacion_empresa'),
path('responder/<int:solicitud_id>/', responder_solicitud_web, name='responder_solicitud_web'),
# etc...
```

---

## 6. DUPLICACIÓN DE URL PARA ELIMINAR VENTA 🔄

### Problema
Misma vista mapeada a dos URLs diferentes.

### Código (empresa/urls.py, líneas 95-96)
```python
path('venta/<int:venta_id>/eliminar/', eliminar_venta, name='eliminar_venta'),
path('api/venta/<int:venta_id>/eliminar/', eliminar_venta, name='api_eliminar_venta'),
```

### Impacto
- 🔄 Confusión sobre cuál URL usar
- 🔄 Inconsistencia en el frontend
- 🔄 Mantenimiento duplicado

### Solución
```python
# Opción A: Usar solo la API
path('api/venta/<int:venta_id>/eliminar/', eliminar_venta, name='eliminar_venta'),

# Opción B: Separar lógica
path('venta/<int:venta_id>/eliminar/', eliminar_venta_web, name='eliminar_venta'),
path('api/venta/<int:venta_id>/eliminar/', eliminar_venta_api, name='api_eliminar_venta'),
```

---

## 7. VALIDACIÓN INSUFICIENTE EN SIMULACIONES 🎮

### Problema
`simulacion_finalizar` no valida que la simulación no esté ya completada.

### Archivo
`empresa/api/views.py`, línea 120-140

### Riesgo
- 🎮 Procesamiento duplicado
- 🎮 XP otorgado múltiples veces
- 🎮 Inconsistencia en datos

### Solución
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulacion_finalizar(request, simulacion_id):
    simulacion = get_object_or_404(
        SimulacionUsuario, 
        id=simulacion_id, 
        usuario=request.user
    )
    
    # AGREGAR VALIDACIÓN
    if simulacion.completada:
        return Response(
            {'error': 'Esta simulación ya fue completada'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Resto del código...
```

---

## 8. SERVICIOS DUPLICADOS 📁

### Problema
Dos archivos con funcionalidad similar.

### Archivos
- `empresa/services/recomendacion_service.py`
- `empresa/services/recommendation_service.py`

### Impacto
- 📁 Confusión sobre cuál usar
- 📁 Posible código duplicado
- 📁 Mantenimiento doble

### Solución
```bash
# Revisar ambos archivos
# Consolidar en uno solo (preferiblemente recommendation_service.py)
# Actualizar imports en todo el proyecto
```

---

## PLAN DE ACCIÓN INMEDIATO

### 🔥 HOY (Crítico)
1. ✅ Decidir sobre manufactura: habilitar o remover del menú
2. ✅ Proteger endpoints de debug con `staff_member_required` o `if DEBUG`
3. ✅ Agregar validación en `simulacion_finalizar`

### 📅 ESTA SEMANA (Urgente)
4. ✅ Refactorizar importaciones lambda
5. ✅ Implementar paginación en APIs principales
6. ✅ Revisar y corregir CSRF exempt

### 📆 ESTE MES (Importante)
7. ✅ Consolidar servicios duplicados
8. ✅ Resolver duplicación de URL eliminar venta
9. ✅ Agregar tests para validar correcciones

---

## COMANDOS PARA VERIFICAR

### Verificar enlaces rotos
```bash
# Iniciar servidor
python manage.py runserver

# En otro terminal, probar URLs
curl -I http://localhost:8000/app-beta-2024/manufactura/
curl -I http://localhost:8000/app-beta-2024/test/filtros/
curl -I http://localhost:8000/app-beta-2024/debug/datos/
```

### Ejecutar tests
```bash
# Tests existentes
python manage.py test empresa.tests

# Verificar cobertura
pip install coverage
coverage run --source='empresa' manage.py test empresa
coverage report
```

### Verificar seguridad
```bash
pip install bandit
bandit -r empresa/ -f json -o security_report.json
```

---

## CONTACTO Y SEGUIMIENTO

Para reportar problemas adicionales o consultas:
- Crear issue en el repositorio
- Documentar en `TODO.md`
- Actualizar este documento con nuevos hallazgos

---

**Última actualización:** 2025
**Próxima revisión:** Después de implementar correcciones críticas
