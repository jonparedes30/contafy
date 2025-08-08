# CONTAFY - Despliegue para Pruebas Reales

## 🚀 **OPCIONES PARA PONER EN PRUEBAS**

### **Opción 1: Heroku (GRATIS - RECOMENDADO)**

#### **Pasos:**
1. **Crear cuenta en Heroku** (heroku.com)
2. **Instalar Heroku CLI**
3. **Preparar archivos**:

```bash
# requirements.txt (agregar)
gunicorn==20.1.0
whitenoise==6.2.0
dj-database-url==1.0.0

# Procfile (crear)
web: gunicorn contafy.wsgi

# runtime.txt (crear)
python-3.12.0
```

4. **Configurar settings.py**:
```python
import dj_database_url
import os

# Producción
DEBUG = False
ALLOWED_HOSTS = ['tu-app.herokuapp.com', 'localhost']

# Base de datos
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
}

# Archivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

5. **Desplegar**:
```bash
git init
git add .
git commit -m "Initial commit"
heroku create contafy-pruebas
git push heroku main
heroku run python manage.py migrate
```

**Resultado**: `https://contafy-pruebas.herokuapp.com`

---

### **Opción 2: Railway (GRATIS)**

1. **Ir a railway.app**
2. **Conectar GitHub**
3. **Deploy automático**
4. **URL generada**: `https://contafy-production.up.railway.app`

---

### **Opción 3: PythonAnywhere (GRATIS)**

1. **Crear cuenta en pythonanywhere.com**
2. **Subir código**
3. **Configurar web app**
4. **URL**: `https://tuusuario.pythonanywhere.com`

---

## 📱 **CONFIGURACIÓN PARA PRUEBAS MÓVILES**

### **1. Actualizar URLs en PWA**
```javascript
// En staticfiles/sw.js
const API_BASE = 'https://contafy-pruebas.herokuapp.com';
```

### **2. Configurar CORS**
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "https://contafy-pruebas.herokuapp.com",
]
```

### **3. HTTPS automático**
- Heroku/Railway dan HTTPS gratis
- PWA requiere HTTPS para funcionar

---

## 👥 **GESTIÓN DE USUARIOS DE PRUEBA**

### **Crear comando para usuarios de prueba**:
```python
# management/commands/crear_usuarios_prueba.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from empresa.models import Empresa

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Crear empresas de prueba
        empresas = [
            {'nombre': 'Panadería El Sol', 'categoria': 'comercial'},
            {'nombre': 'Textiles Andinos', 'categoria': 'manufactura'},
            {'nombre': 'Consultora ABC', 'categoria': 'servicios'},
        ]
        
        for i, emp_data in enumerate(empresas, 1):
            empresa = Empresa.objects.create(**emp_data)
            user = User.objects.create_user(
                username=f'prueba{i}',
                password='prueba123',
                email=f'prueba{i}@contafy.com'
            )
            user.empresa = empresa
            user.save()
            
        self.stdout.write('Usuarios de prueba creados')
```

**Ejecutar**:
```bash
python manage.py crear_usuarios_prueba
```

---

## 📋 **PLAN DE PRUEBAS**

### **Usuarios de Prueba**:
- **prueba1** / prueba123 (Comercial)
- **prueba2** / prueba123 (Manufactura)  
- **prueba3** / prueba123 (Servicios)

### **Tareas para testers**:
1. **Registro/Login**
2. **Crear productos/materias primas**
3. **Registrar ventas**
4. **Ver reportes**
5. **Probar en móvil** (instalar PWA)

### **Feedback a recopilar**:
- Facilidad de uso
- Errores encontrados
- Funciones faltantes
- Rendimiento móvil

---

## 🔧 **ARCHIVOS A CREAR**

### **requirements.txt** (actualizar):
```
Django==5.2.3
psycopg2-binary==2.9.7
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
django-cors-headers==4.3.1
openpyxl==3.1.2
reportlab==4.0.4
Pillow==10.0.1
requests==2.31.0
pandas==2.1.1
matplotlib==3.7.2
numpy==1.25.2
jazzmin==2.6.0
gunicorn==20.1.0
whitenoise==6.2.0
dj-database-url==1.0.0
```

### **Procfile**:
```
web: gunicorn contafy.wsgi
```

### **runtime.txt**:
```
python-3.12.0
```

---

## ⏱️ **CRONOGRAMA**

| Día | Actividad |
|-----|-----------|
| **Día 1** | Configurar Heroku y desplegar |
| **Día 2** | Crear usuarios de prueba |
| **Día 3** | Invitar 5-10 testers |
| **Día 4-10** | Período de pruebas |
| **Día 11** | Recopilar feedback |
| **Día 12-14** | Corregir errores |

---

## 💰 **COSTOS**

- **Heroku**: GRATIS (hasta 1000 horas/mes)
- **Railway**: GRATIS (hasta $5 crédito)
- **PythonAnywhere**: GRATIS (limitado)

**Recomendación**: Empezar con Heroku (más fácil)