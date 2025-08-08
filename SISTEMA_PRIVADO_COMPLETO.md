# CONTAFY - Sistema Privado con Invitaciones

## 🔒 **CÓMO FUNCIONA EL SISTEMA PRIVADO**

### **1. URL Secreta**
- URL pública: `https://contafy-pruebas.herokuapp.com/app-beta-2024/`
- Solo quien tenga este link puede acceder
- No aparece en Google ni buscadores

### **2. Códigos de Invitación**
- Cada persona necesita un código único para registrarse
- Los códigos se usan una sola vez
- Tú generas los códigos y los envías

---

## 🚀 **IMPLEMENTACIÓN PASO A PASO**

### **Paso 1: Generar códigos de invitación**
```bash
# En tu servidor/local
python manage.py generar_codigos 10

# Resultado:
# - CONTAFY-ABC123XYZ
# - CONTAFY-DEF456UVW
# - CONTAFY-GHI789RST
# ... (10 códigos únicos)
```

### **Paso 2: Enviar invitaciones**
**Email/WhatsApp a tus testers:**
```
¡Hola! Te invito a probar CONTAFY (sistema contable).

🔗 Link: https://contafy-pruebas.herokuapp.com/app-beta-2024/
🔑 Tu código: CONTAFY-ABC123XYZ

Pasos:
1. Abrir el link
2. Hacer clic en "Registrarse"
3. Llenar datos + tu código
4. ¡Listo para probar!

Móvil: Puedes instalarlo como app desde el navegador.
```

### **Paso 3: Control total**
- ✅ Solo 10 personas pueden registrarse (o las que quieras)
- ✅ Cada código funciona una sola vez
- ✅ URL secreta que solo tú conoces
- ✅ Puedes generar más códigos cuando quieras

---

## 📱 **EXPERIENCIA DEL USUARIO**

### **Usuario recibe invitación:**
1. Abre link secreto
2. Ve página de registro con campo "Código de Invitación"
3. Ingresa su código único
4. Se registra normalmente
5. Puede usar web y móvil

### **Si alguien encuentra la URL sin código:**
- No puede registrarse (necesita código válido)
- Solo puede ver página de login
- Sin código = sin acceso

---

## 🎯 **VENTAJAS DE ESTE SISTEMA**

### **Para ti:**
- ✅ Control total de quién accede
- ✅ Sabes exactamente cuántos usuarios tienes
- ✅ Puedes rastrear quién usó cada código
- ✅ Fácil de gestionar

### **Para los testers:**
- ✅ Proceso simple de registro
- ✅ Se sienten "especiales" (invitación exclusiva)
- ✅ Funciona en web y móvil
- ✅ Pueden crear su propia empresa

---

## 🔧 **ARCHIVOS A MODIFICAR**

1. **Agregar modelo** `CodigoInvitacion` a `models.py`
2. **Modificar vista** de registro en `autenticacion.py`
3. **Cambiar URL** principal en `urls.py`
4. **Actualizar template** de registro
5. **Crear comando** para generar códigos

---

## 📊 **PANEL DE CONTROL**

```bash
# Ver códigos disponibles
python manage.py shell -c "from empresa.models import CodigoInvitacion; print('Disponibles:', CodigoInvitacion.objects.filter(usado=False).count())"

# Ver quién se registró
python manage.py shell -c "from empresa.models import CodigoInvitacion; [print(f'{c.codigo}: {c.usado_por.username if c.usado_por else \"No usado\"}') for c in CodigoInvitacion.objects.all()]"

# Generar más códigos
python manage.py generar_codigos 5
```

---

## ✅ **RESULTADO FINAL**

**Tu sistema será:**
- 🔒 **100% Privado** - Solo invitados
- 🎯 **Controlado** - Tú decides quién entra
- 📱 **Móvil** - PWA funcional
- 🌐 **Web** - Acceso desde cualquier navegador
- 📊 **Rastreable** - Sabes quién usa qué código

**¿Implementamos este sistema privado con códigos de invitación?**