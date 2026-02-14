# GUÍA TÉCNICA - REPARACIÓN DE MIGRACIONES
## Cómo arreglar los gaps en Django Migrations

**Fecha**: 2026-02-13  
**Problema**: Migraciones faltantes (0007-0014, 0019-0020)  
**Solución**: Crear migraciones vacías para restaurar secuencia  
**Tiempo estimado**: 30-45 minutos  

---

## 🔍 PROBLEMA IDENTIFICADO

```
Cadena actual (ROTA):
0001 → 0002 → 0003 → 0004 → 0005 → 0006 → [FALTA 0007-0014] → 0015
                                                 ↓
                              Dependencies apunta directamente a 0006

Cuando Django intenta `migrate` en BD limpia:
Django carga 0001, 0002, ..., 0006 OK
Django espera 0007 (no existe)
❌ FAIL: "No migration with name '0007_*'"
```

---

## ✅ SOLUCIÓN: Crear Migraciones Vacías

### Paso 1: Crear Migraciones 0007-0014 (vacías)

Voy a crear un script Python que genere estas migraciones:

```python
# scripts/fix_migrations.py (crear este archivo)
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BASE_DIR / 'empresa' / 'migrations'

# Migraciones faltantes a crear
MISSING_RANGES = [
    (7, 14, '0006_codigoinvitacion_tiposervicio_materialservicio'),  # 0007-0014
    (19, 20, '0018_rename_empresa_mov_empresa_b8c123_idx_empresa_mov_empresa_f0e590_idx_and_more'),  # 0019-0020
]

def create_empty_migration(number, depends_on):
    """Crear una migración vacía con dependencia correcta"""
    migration_name = f'{number:04d}_empty.py'
    migration_path = MIGRATIONS_DIR / migration_name
    
    content = f'''# Generated empty migration to maintain sequence
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '{depends_on}'),
    ]

    operations = [
    ]
'''
    
    with open(migration_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Creada: {migration_name}")

# Crear migraciones 0007-0014
for start, end, prev_migration in MISSING_RANGES:
    current_prev = prev_migration
    for i in range(start, end + 1):
        # Generar nombre basado en número anterior
        prev_num = f'{i-1:04d}' if i > start else prev_migration.split('_')[0]
        
        if i > start:
            # Para 0008 en adelante, depender del anterior
            current_prev = f'{prev_num}_empty'
        
        create_empty_migration(f'{i:04d}_empty', current_prev)

print("\n✅ Migraciones vacías creadas exitosamente")
```

### Paso 2: Ejecutar Script

```bash
cd /ruta/a/contafy
python scripts/fix_migrations.py
```

**Resultado esperado**:
```
✓ Creada: 0007_empty.py
✓ Creada: 0008_empty.py
✓ Creada: 0009_empty.py
... (hasta 0014)
✓ Creada: 0019_empty.py
✓ Creada: 0020_empty.py

✅ Migraciones vacías creadas exitosamente
```

### Paso 3: Actualizar Dependencias en 0015 y 0021

**Archivo**: `empresa/migrations/0015_auto_20250822_1526.py`

**Cambiar de**:
```python
dependencies = [
    ('empresa', '0006_codigoinvitacion_tiposervicio_materialservicio'),
]
```

**Cambiar a**:
```python
dependencies = [
    ('empresa', '0014_empty'),  # Ahora depende de 0014 (último de la secuencia)
]
```

---

**Archivo**: `empresa/migrations/0021_add_accounting_setup.py`

**Cambiar de**:
```python
dependencies = [
    ('empresa', '0018_rename_empresa_mov_empresa_b8c123_idx_empresa_mov_empresa_f0e590_idx_and_more'),
]
```

**Cambiar a**:
```python
dependencies = [
    ('empresa', '0020_empty'),  # Ahora depende de 0020 (último de la secuencia)
]
```

---

### Paso 4: Verificar Secuencia

```bash
python manage.py showmigrations empresa

# Esperado:
#  [X] 0001_initial
#  [X] 0002_capital_...
#  ...
#  [X] 0006_codigoinvitacion_...
#  [X] 0007_empty  ← NUEVA
#  [X] 0008_empty  ← NUEVA
#  [X] 0009_empty  ← NUEVA
#  ...
#  [X] 0014_empty  ← NUEVA
#  [X] 0015_auto_20250822_1526
#  [X] 0016_niif_fase1
#  [X] 0017_niif_fase2
#  [X] 0018_...
#  [X] 0019_empty  ← NUEVA
#  [X] 0020_empty  ← NUEVA
#  [X] 0021_add_accounting_setup
#  ... hasta 0026
```

---

### Paso 5: Probar en BD Limpia

```bash
# 1. Copiar entorno a uno temporal
cp -r contafy contafy-test

# 2. Recrear .venv
cd contafy-test
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows

# 3. Instalar requirements
pip install -r requirements.txt

# 4. Configurar .env (SQLite)
cp .env.example .env
# (dejar DATABASE_URL vacío para usar SQLite)

# 5. Aplicar migraciones
python manage.py migrate

# Esperado:
# Operations to perform:
#   Apply all migrations: ...
# Running migrations:
#   Applying empresa.0001_initial ... OK
#   Applying empresa.0002_capital_... ... OK
#   ... (todas las migraciones)
#   Applying empresa.0026_alter_venta_tipo_pago ... OK
# ✅ SUCCESS

# 6. Verificar tablas creadas
python manage.py shell
>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
# Debe haber 20+ tablas

# 7. Prueba final
python manage.py check
python manage.py runserver
# http://127.0.0.1:8000 debe cargar sin errores
```

---

## 🎯 ALTERNATIVA: Si Quieres Ser Más Específico

Si quieres que las migraciones vacías tengan nombres más descriptivos (en lugar de "empty"):

### Opción A: Migraciones con operaciones de 0015

En vez de crear vacías, podrías "extraer" las operaciones de 0015 a las migraciones 0007-0014.

**Pero es MÁS COMPLEJO** porque:
- Necesitas entender qué cambios hace 0015
- Riesgo de cambiar lógica de cambios

**Recomendación**: Mantener vacías (es más seguro)

---

## 🔍 VERIFICACIÓN POST-REPARACIÓN

```bash
# 1. Migraciones secuenciales sin gaps
python manage.py showmigrations | grep empresa

# 2. Dependencias correctas
grep -r "dependencies" empresa/migrations/*.py

# 3. BD limpia funciona
python manage.py migrate --plan  # Sin errores
python manage.py migrate        # Aplica exitosamente

# 4. Servidor inicia
python manage.py runserver     # Sin errores de BD

# 5. Admin funciona
# Ir a http://127.0.0.1:8000/admin
# Debe cargar sin errores
```

---

## ⚠️ IMPACTO EN BD EXISTENTE

**¿Qué pasa si ya corriste migraciones en tu BD actual?**

Las migraciones ya están marcadas como aplicadas (`[X]` en `django_migrations`), así que:

```bash
python manage.py migrate
# NO aplicará 0007-0014, 0019-0020 (ya están en historial)
# Aplicará migraciones nuevas desde 0026
```

**No rompe BD existente** ✅

---

## 📋 CHECKLIST DE COMPLECIÓN

- [ ] Script `fix_migrations.py` ejecutado
- [ ] 8 archivos creados: 0007-0014.py
- [ ] 2 archivos creados: 0019-0020.py
- [ ] 0015_auto_20250822_1526.py actualizado
- [ ] 0021_add_accounting_setup.py actualizado
- [ ] Prueba en BD limpia exitosa
- [ ] `showmigrations` muestra secuencia completa
- [ ] Servidor inicia sin errores
- [ ] Commit a Git: "Fix migration sequence gaps (0007-0014, 0019-0020)"

---

## 🚀 DESPUÉS DE REPARAR

Una vez completado:

```
git add empresa/migrations/
git add scripts/fix_migrations.py
git commit -m "Fix: Restore migration sequence gaps (0007-0014, 0019-0020)"
git push origin main
```

**En otra máquina**:
```bash
git clone <repo>
python -m venv .venv
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate  # ✅ FUNCIONA AHORA
python manage.py runserver
```

---

## 📞 VALIDACIÓN

Si todo funciona correctamente:
- ✅ Migraciones no tienen gaps
- ✅ BD limpia se puede crear desde cero
- ✅ Proyecto es reproducible en máquina nueva
- ✅ **NIVEL 3 alcanzado** (Reproducible profesional)

---

**Guía técnica completada**: 2026-02-13  
**Próximo paso**: Ejecutar pasos arriba descritos

