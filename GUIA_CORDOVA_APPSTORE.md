# Guía Completa: CONTAFY en App Stores

## ✅ **SÍ, se puede publicar en App Stores**

### **Pasos para implementar Cordova:**

#### 1. **Instalación** (Ejecutar en terminal):
```bash
# Instalar Node.js primero (nodejs.org)
npm install -g cordova

# Crear proyecto
cordova create ContafyApp com.contafy.app CONTAFY
cd ContafyApp

# Agregar plataformas
cordova platform add android
cordova platform add ios
```

#### 2. **Configurar archivos**:
- Copiar `config.xml` a la carpeta ContafyApp/
- Copiar `cordova_index.html` como `www/index.html`
- Agregar iconos en `res/icon/`

#### 3. **Compilar**:
```bash
# Para Android
cordova build android

# Para iOS (solo en Mac)
cordova build ios
```

---

## **📱 Publicación en App Stores**

### **Google Play Store (Android)**
**Requisitos:**
- Cuenta de desarrollador: $25 USD (una vez)
- Archivo APK compilado
- Iconos y screenshots
- Descripción de la app

**Pasos:**
1. Compilar: `cordova build android --release`
2. Firmar APK con certificado
3. Subir a Google Play Console
4. Revisión: 1-3 días
5. ✅ **App disponible para descarga**

### **Apple App Store (iOS)**
**Requisitos:**
- Mac con Xcode
- Cuenta de desarrollador: $99 USD/año
- Certificados de desarrollo

**Pasos:**
1. Compilar: `cordova build ios`
2. Abrir en Xcode
3. Configurar certificados
4. Subir a App Store Connect
5. Revisión: 1-7 días
6. ✅ **App disponible para descarga**

---

## **🔧 Configuración API Django**

Para que la app funcione, necesitas:

```python
# En settings.py
CORS_ALLOWED_ORIGINS = [
    "file://",  # Para Cordova
]

# Nueva vista API para login móvil
@csrf_exempt
def mobile_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = authenticate(
            username=data['username'], 
            password=data['password']
        )
        if user:
            token = generate_token(user)
            return JsonResponse({
                'success': True,
                'token': token,
                'empresa': user.empresa.nombre
            })
        return JsonResponse({'success': False})
```

---

## **💰 Costos totales:**

- **Google Play**: $25 USD (una vez)
- **Apple Store**: $99 USD/año
- **Desarrollo**: 1-2 semanas
- **Mantenimiento**: Mínimo

---

## **🚀 Ventajas de tener app en stores:**

✅ **Descarga desde tiendas oficiales**  
✅ **Mayor confianza de usuarios**  
✅ **Notificaciones push**  
✅ **Actualizaciones automáticas**  
✅ **Acceso offline mejorado**  
✅ **Integración con sistema operativo**  

---

## **Próximos pasos:**

1. **Ejecutar**: `cordova_setup.bat`
2. **Configurar**: API endpoints
3. **Compilar**: Apps para Android/iOS
4. **Publicar**: En las tiendas

**¿Quieres que proceda con la implementación?**