# Guía para Convertir CONTAFY en App Móvil

## Opción 1: PWA (Progressive Web App) - IMPLEMENTADA ✅

### Qué es:
Una PWA permite que tu web funcione como app nativa sin necesidad de tiendas de apps.

### Cómo instalar en el teléfono:
1. **Android**: Abrir en Chrome → Menú → "Agregar a pantalla de inicio"
2. **iOS**: Abrir en Safari → Compartir → "Agregar a pantalla de inicio"

### Ventajas:
- ✅ Sin tiendas de apps
- ✅ Actualizaciones automáticas
- ✅ Funciona offline (básico)
- ✅ Icono en pantalla de inicio
- ✅ Pantalla completa

## Opción 2: App Nativa con React Native

### Pasos:
```bash
# 1. Instalar React Native
npm install -g react-native-cli

# 2. Crear proyecto
npx react-native init ContafyApp

# 3. Instalar dependencias
npm install axios react-navigation
```

### Estructura básica:
```javascript
// App.js
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import MateriasScreen from './screens/MateriasScreen';
import VentasScreen from './screens/VentasScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Tab.Navigator>
        <Tab.Screen name="Materias" component={MateriasScreen} />
        <Tab.Screen name="Ventas" component={VentasScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
```

## Opción 3: App Híbrida con Cordova/PhoneGap

### Pasos:
```bash
# 1. Instalar Cordova
npm install -g cordova

# 2. Crear proyecto
cordova create ContafyApp com.contafy.app CONTAFY

# 3. Agregar plataformas
cordova platform add android ios

# 4. Copiar archivos web a www/
# 5. Compilar
cordova build android
```

## Recomendación:

**Para tu caso, usa PWA (ya implementada)** porque:
- ✅ Más rápido de implementar
- ✅ Sin costos de tiendas de apps
- ✅ Actualizaciones instantáneas
- ✅ Funciona en iOS y Android
- ✅ Mantiene toda la funcionalidad web

## Archivos creados para PWA:
- `manifest.json` - Configuración de la app
- `sw.js` - Service worker para cache
- Meta tags en templates

## Próximos pasos:
1. Crear iconos (192x192 y 512x512 px)
2. Probar en dispositivos móviles
3. Optimizar para offline (opcional)