# CONTAFY - Sistema Privado con Heroku

## 🔒 **SISTEMA ACTUAL (PRIVADO CON INVITACIONES)**

### **Configuración Implementada:**
- **URL Secreta**: `/app-beta-2024/` (en lugar de `/empresa/`)
- **Códigos de Invitación**: Obligatorios para registro
- **Acceso Controlado**: Solo invitados pueden registrarse

### **Archivos Modificados para Sistema Privado:**
```
core/urls.py - URL secreta
empresa/models.py - Modelo CodigoInvitacion
empresa/views/autenticacion.py - Validación códigos
empresa/templates/empresa/registro.html - Campo código
empresa/management/commands/generar_codigos.py - Comando códigos
```

---

## 🚀 **PASOS PARA SUBIR A HEROKU CON BLOQUEO**

### **1. Preparar Heroku**
```bash
# Instalar Heroku CLI desde heroku.com
# Crear cuenta gratuita

# Login
heroku login
```

### **2. Preparar Proyecto**
```bash
# En carpeta del proyecto
git init
git add .
git commit -m "Sistema privado con invitaciones"
```

### **3. Crear App en Heroku**
```bash
heroku create contafy-pruebas
```

### **4. Configurar Variables de Entorno**
```bash
heroku config:set DEBUG=False
heroku config:set SECRET_KEY="tu-clave-secreta-aqui"
```

### **5. Desplegar**
```bash
git push heroku main
```

### **6. Configurar Base de Datos**
```bash
heroku run python manage.py migrate
```

### **7. Generar Códigos de Invitación**
```bash
heroku run python manage.py generar_codigos 10
```

### **8. ¡LISTO!**
- **URL**: `https://contafy-pruebas.herokuapp.com/app-beta-2024/`
- **Sistema**: Privado con códigos de invitación
- **Acceso**: Solo invitados

---

## 📧 **ENVIAR INVITACIONES A TESTERS**

### **Mensaje Tipo:**
```
🎉 Te invito a probar CONTAFY (sistema contable)

🔗 Link: https://contafy-pruebas.herokuapp.com/app-beta-2024/
🔑 Tu código: CONTAFY-ABC123XYZ

Pasos:
1. Abrir el link
2. Hacer clic en "Registrarse"
3. Llenar datos + tu código único
4. ¡Probar el sistema!

📱 Funciona en móvil: Puedes instalarlo como app desde el navegador.
```

---

## 🔧 **COMANDOS ÚTILES EN HEROKU**

```bash
# Ver logs
heroku logs --tail

# Generar más códigos
heroku run python manage.py generar_codigos 20

# Ver códigos disponibles
heroku run python manage.py shell -c "from empresa.models import CodigoInvitacion; print('Disponibles:', CodigoInvitacion.objects.filter(usado=False).count())"

# Reiniciar app
heroku restart
```

---

## 🔄 **CÓMO REVERTIR A SISTEMA PÚBLICO**

### **Cuando quieras hacer el sistema público:**

#### **1. Cambiar URL Principal**
```python
# En core/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('empresa.urls')),  # Cambiar de 'app-beta-2024/' a ''
]
```

#### **2. Remover Validación de Códigos**
```python
# En empresa/views/autenticacion.py
def registrar_usuario(request):
    if request.method == 'POST':
        # REMOVER TODA LA VALIDACIÓN DE CÓDIGOS
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Cuenta y empresa creadas exitosamente.')
            return redirect('empresa:login')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = RegistroForm()
    return render(request, 'empresa/registro.html', {
        'form': form,
    })
```

#### **3. Remover Campo Código del Template**
```html
<!-- En empresa/templates/empresa/registro.html -->
<!-- ELIMINAR TODA LA SECCIÓN DE CÓDIGO DE INVITACIÓN -->
```

#### **4. Desplegar Cambios**
```bash
git add .
git commit -m "Sistema público - sin códigos de invitación"
git push heroku main
```

#### **5. Resultado:**
- **URL pública**: `https://contafy-pruebas.herokuapp.com/`
- **Registro libre**: Sin códigos necesarios
- **Acceso abierto**: Cualquiera puede registrarse

---

## 📊 **COMPARACIÓN SISTEMAS**

| Aspecto | Sistema Privado (Actual) | Sistema Público (Futuro) |
|---------|-------------------------|-------------------------|
| **URL** | `/app-beta-2024/` | `/` |
| **Registro** | Con código obligatorio | Libre |
| **Acceso** | Solo invitados | Cualquiera |
| **Control** | Total | Ninguno |
| **Uso** | Pruebas controladas | Producción abierta |

---

## 💡 **RECOMENDACIONES**

### **Para Pruebas (Ahora):**
- Usar sistema privado
- Invitar 10-20 testers
- Recopilar feedback
- Corregir errores

### **Para Producción (Después):**
- Revertir a sistema público
- URL principal simple
- Marketing y promoción
- Registro abierto

---

## 🎯 **ARCHIVOS DE RESPALDO**

### **Antes de revertir, respaldar:**
```bash
# Crear branch de respaldo
git checkout -b sistema-privado-respaldo
git push heroku sistema-privado-respaldo

# Volver a main para hacer público
git checkout main
```

**Este README te permite implementar el sistema privado en Heroku y revertirlo cuando sea necesario.**