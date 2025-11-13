# Crear Códigos de Invitación en Render

## Opción 1: Desde el Shell de Render (RECOMENDADO)

1. Ve a tu servicio en Render: https://dashboard.render.com/
2. Selecciona el servicio `contafy`
3. Ve a la pestaña **Shell**
4. Ejecuta este comando:

```python
python manage.py shell -c "
from empresa.models import CodigoInvitacion
import random, string

def gen():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

codigos = []
for i in range(20):
    while True:
        c = gen()
        if not CodigoInvitacion.objects.filter(codigo=c).exists():
            break
    CodigoInvitacion.objects.create(codigo=c)
    codigos.append(c)
    print(f'✅ {i+1}. {c}')

print(f'\n🎉 {len(codigos)} códigos creados!')
"
```

## Opción 2: Después del Deploy

Una vez que el deploy termine (con los cambios del admin), ejecuta localmente:

```powershell
# Configurar para conectar a Render
$env:DATABASE_URL="postgresql://contafy_db_user:ycmaEMIJ9ZlAuFYQ6VVqaGqnnZdyR80D@dpg-d4aeou2li9vc73fgr0k0-a/contafy_db"
python crear_codigos_render.py 20
```

## Verificar en Admin

Los códigos aparecerán en:
- **URL**: https://contafy.onrender.com/admin/empresa/codigoinvitacion/
- **Usuario**: Tu superusuario
- **Funciones**: Ver, filtrar, buscar, marcar como no usado

## Crear Superusuario (si no existe)

Si no tienes superusuario en Render, desde el Shell ejecuta:

```bash
python manage.py createsuperuser
```
