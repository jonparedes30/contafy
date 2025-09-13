# Migraciones Pendientes - Academia CONTAFY

## Comandos para aplicar migraciones

```powershell
# 1. Crear migraciones para nuevos campos
$env:DJANGO_SETTINGS_MODULE='core.test_settings'
python manage.py makemigrations empresa --name add_audit_and_slug_fields

# 2. Aplicar migraciones
python manage.py migrate

# 3. Verificar migraciones aplicadas
python manage.py showmigrations empresa

# 4. Limpiar variable de entorno
Remove-Item Env:\DJANGO_SETTINGS_MODULE
```

## Nuevos campos agregados

### ModuloAprendizaje
- `slug` (SlugField, unique=True)
- `visible` (BooleanField, default=True)
- `creado_en` (DateTimeField, auto_now_add=True)
- `actualizado_en` (DateTimeField, auto_now=True)

### Leccion
- `slug` (SlugField, max_length=220)
- `creado_en` (DateTimeField, auto_now_add=True)
- `actualizado_en` (DateTimeField, auto_now=True)
- Índices: `[modulo, orden]`, `[tipo, visible]`
- Constraint: `unique_together = [['slug', 'modulo']]`

### AsientoAudit (nuevo modelo)
- `simulacion` (FK a SimulacionUsuario)
- `cuenta` (CharField, max_length=100)
- `tipo_cuenta` (CharField, max_length=20)
- `tipo_movimiento` (CharField, max_length=10)
- `monto` (DecimalField, max_digits=12, decimal_places=2)
- `descripcion` (TextField)
- `transaccion_id` (CharField, max_length=50)
- `creado_en` (DateTimeField, auto_now_add=True)
- Índices: `[simulacion, transaccion_id]`, `[tipo_movimiento, creado_en]`

## Tests para ejecutar después de migraciones

```powershell
$env:DJANGO_SETTINGS_MODULE='core.test_settings'

# Tests de modelos
python manage.py test empresa.tests.test_models_aprendizaje -v 2

# Tests de sandbox
python manage.py test empresa.tests.test_sandbox_hardening -v 2

# Tests de AsientoAudit
python manage.py test empresa.tests.test_asiento_audit -v 2

Remove-Item Env:\DJANGO_SETTINGS_MODULE
```

## Validación post-migración

1. **Admin funcional**: Verificar que el admin carga sin errores
2. **Comando demo**: `python manage.py crear_contenido_demo`
3. **Slugs auto-generados**: Crear módulo/lección y verificar slug
4. **AsientoAudit**: Ejecutar simulación sandbox y verificar audit logs