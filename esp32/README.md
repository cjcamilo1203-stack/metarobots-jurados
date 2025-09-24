# 🤖 ESP32 - Códigos de Ejemplo para MetaRobots

Esta carpeta contiene ejemplos de código Arduino para ESP32 que se conectan al sistema MetaRobots Jurados.

## 📁 Archivos Incluidos

### 1. `metarobots_client.ino` - **Ejemplo Completo**

- ✅ Sistema completo con WiFi, botones, LED y comandos seriales
- ✅ Manejo de errores robusto
- ✅ Indicaciones visuales con LED
- ✅ Comandos por Serial Monitor
- ✅ Documentación extensa

### 2. `ejemplo_simple.ino` - **Ejemplo Básico**

- ✅ Código minimalista para pruebas rápidas
- ✅ Envía tiempo automáticamente cada 10 segundos
- ✅ Ideal para entender el funcionamiento básico

## 🔧 Configuración Requerida

### Librerías Arduino

Instala desde el Library Manager:

- **ArduinoJson** (por Benoit Blanchon)
- WiFi y HTTPClient (incluidas en ESP32 Core)

### Configuración en el Código

```cpp
// Cambia estos valores por los tuyos:
const char* ssid = "TU_WIFI_AQUI";
const char* password = "TU_PASSWORD_AQUI";
const char* serverURL = "http://IP_DEL_SERVIDOR:8000/api/registrar-tiempo/";
// Ejemplo: "http://192.168.1.100:8000/api/registrar-tiempo/"
```

> **Nota:** Reemplaza `IP_DEL_SERVIDOR` con la IP real de tu computadora donde corre Django. Puedes obtenerla ejecutando `ipconfig` en Windows o `ifconfig` en Linux/Mac.

## 🌐 API Endpoint

**URL:** `http://192.168.0.122:8000/api/registrar-tiempo/`

**Método:** POST

**JSON Requerido:**

```json
{
  "categoria": "velocista",
  "tiempo": "12.34567"
}
```

**Categorías válidas:**

- `"velocista"` - Para robots velocistas
- `"rally"` - Para robots rally

## 🚀 Uso Rápido

### Opción 1: Ejemplo Simple

1. Abre `ejemplo_simple.ino`
2. Cambia WiFi y contraseña
3. Sube a la ESP32
4. En el web: ve a un robot → "Registrar Tiempo"
5. El ESP32 enviará automáticamente tiempos

### Opción 2: Ejemplo Completo

1. Abre `metarobots_client.ino`
2. Configura WiFi y servidor
3. Sube a la ESP32
4. Usa botón BOOT o comandos seriales
5. Monitorea respuestas en Serial Monitor

## 📊 Comandos Seriales (Ejemplo Completo)

Abre Serial Monitor a 115200 baudios:

- `test` - Enviar tiempo aleatorio
- `status` - Ver estado del sistema
- `help` - Ver todos los comandos
- Botón BOOT - Enviar tiempo manualmente

## 🔍 Respuestas del Servidor

### ✅ Éxito (200)

```json
{
  "success": true,
  "robot": "Lightning McQueen",
  "tiempo": "12.34567",
  "categoria": "velocista"
}
```

### ❌ Error Común (400)

```json
{
  "success": false,
  "error": "No hay sesión activa esperando tiempo para la categoría velocista"
}
```

**Solución:** Asegúrate de hacer clic en "Registrar Tiempo" en el sistema web antes de enviar desde ESP32.

## 🚨 Solución de Problemas

### Error de Conexión WiFi

- ✅ Verifica SSID y contraseña
- ✅ Asegúrate de que ESP32 esté en rango
- ✅ Prueba con un hotspot móvil

### Error HTTP 400

- ✅ Debe haber una sesión activa esperando
- ✅ Verifica que la categoría sea correcta
- ✅ Solo una sesión por categoría a la vez

### Error de Conexión al Servidor

- ✅ Verifica que Django esté ejecutándose
- ✅ Confirma la IP en `serverURL`
- ✅ Asegúrate de estar en la misma red

### Tiempo no se Registra

- ✅ Formato debe ser string: `"12.34567"`
- ✅ Categoría en minúsculas: `"velocista"` o `"rally"`
- ✅ Content-Type debe ser `"application/json"`

## 🔄 Flujo de Funcionamiento

1. **ESP32 se conecta a WiFi**
2. **Jurado activa "Registrar Tiempo" en el web**
3. **ESP32 envía JSON con tiempo**
4. **Servidor valida y registra el tiempo**
5. **Servidor responde con confirmación**
6. **Sesión se cierra automáticamente**

## 🎯 Notas Importantes

- ⚠️ **Solo funciona con sesión activa** - Alguien debe estar esperando el tiempo
- ⚠️ **Una sesión por categoría** - Solo puede haber una sesión activa por categoría
- ⚠️ **IP correcta** - Usa la IP de red, no localhost
- ⚠️ **Mismo WiFi** - ESP32 y servidor deben estar en la misma red

## 🧪 Ejemplo de JSON Enviado

```json
{
  "categoria": "velocista",
  "tiempo": "12.34567"
}
```

Este JSON se envía exactamente como especificaste en tu solicitud a:
`http://192.168.0.122:8000/api/registrar-tiempo/`

¡Los códigos están listos para usar en tu competencia de robots! 🏆
