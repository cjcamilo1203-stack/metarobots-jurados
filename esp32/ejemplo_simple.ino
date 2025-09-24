/*
 * MetaRobots - Ejemplo Simple ESP32
 * 
 * Ejemplo básico que envía un tiempo cada 10 segundos
 * Ideal para pruebas rápidas y entender el funcionamiento
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ==================== CONFIGURACIÓN BÁSICA ====================
const char* ssid = "TU_WIFI_AQUI";
const char* password = "TU_PASSWORD_AQUI";
const char* serverURL = "http://192.168.0.122:8000/api/registrar-tiempo/";

void setup() {
  Serial.begin(115200);
  
  // Conectar WiFi
  WiFi.begin(ssid, password);
  Serial.print("Conectando a WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("✅ WiFi conectado!");
  Serial.println("📍 IP: " + WiFi.localIP().toString());
  Serial.println("🎯 Enviando tiempo cada 10 segundos...");
}

void loop() {
  // Generar tiempo aleatorio para velocista (8-20 segundos)
  float tiempo = random(800, 2000) / 100.0;
  
  enviarTiempo(tiempo, "velocista");
  
  delay(10000);  // Esperar 10 segundos
}

void enviarTiempo(float tiempo, String categoria) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    
    // Crear JSON exactamente como el ejemplo solicitado
    StaticJsonDocument<200> doc;
    doc["categoria"] = categoria;
    doc["tiempo"] = String(tiempo, 5);  // 5 decimales: "12.34567"
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    Serial.println("📤 Enviando: " + jsonString);
    Serial.println("🌐 A: " + String(serverURL));
    
    int codigo = http.POST(jsonString);
    
    if (codigo > 0) {
      String respuesta = http.getString();
      Serial.println("📨 Respuesta (" + String(codigo) + "): " + respuesta);
      
      if (codigo == 200) {
        Serial.println("✅ ¡Tiempo registrado exitosamente!");
      } else {
        Serial.println("⚠️  Error - Verifica que haya sesión activa");
      }
    } else {
      Serial.println("❌ Error de conexión: " + String(codigo));
    }
    
    http.end();
    Serial.println("---");
  } else {
    Serial.println("❌ WiFi desconectado");
  }
}

/*
 * INSTRUCCIONES:
 * 
 * 1. Cambia "TU_WIFI_AQUI" y "TU_PASSWORD_AQUI" por tus datos reales
 * 
 * 2. Verifica que la IP sea correcta (192.168.0.122)
 * 
 * 3. Instala la librería ArduinoJson desde el Library Manager
 * 
 * 4. En el sistema web:
 *    - Ve a un robot de velocista
 *    - Presiona "Registrar Tiempo"
 *    - El ESP32 enviará automáticamente un tiempo
 * 
 * 5. El código envía este JSON cada 10 segundos:
 *    {
 *        "categoria": "velocista",
 *        "tiempo": "12.34567"
 *    }
 * 
 * Para cambiar a rally, cambia "velocista" por "rally" en el código.
 */
