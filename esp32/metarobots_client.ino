/*
 * MetaRobots - Cliente ESP32 para Sistema de Jurados
 * 
 * Este código envía tiempos registrados al sistema web MetaRobots
 * Ejemplo funcional que publica tiempos a la API REST
 * 
 * Autor: Sistema MetaRobots - Universidad de los Llanos
 * Fecha: Septiembre 2025
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ==================== CONFIGURACIÓN ====================
// WiFi
const char* WIFI_SSID = "TU_WIFI_AQUI";           // Cambiar por tu WiFi
const char* WIFI_PASSWORD = "TU_PASSWORD_AQUI";   // Cambiar por tu contraseña

// Servidor MetaRobots
const char* SERVER_URL = "http://192.168.0.122:8000/api/registrar-tiempo/";
const String CATEGORIA = "velocista";  // Cambiar por "rally" si es necesario

// Pines
const int BUTTON_PIN = 0;      // Pin del botón (GPIO0 - botón BOOT)
const int LED_PIN = 2;         // Pin del LED integrado
const int SENSOR_PIN = 4;      // Pin del sensor (opcional)

// Variables
bool buttonPressed = false;
unsigned long lastButtonTime = 0;
const unsigned long DEBOUNCE_DELAY = 500;  // 500ms debounce

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("===========================================");
  Serial.println("🤖 MetaRobots - Cliente ESP32");
  Serial.println("   Universidad de los Llanos");
  Serial.println("===========================================");
  
  // Configurar pines
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  pinMode(SENSOR_PIN, INPUT_PULLUP);
  
  // Conectar a WiFi
  conectarWiFi();
  
  Serial.println();
  Serial.println("📋 Configuración:");
  Serial.println("   - Servidor: " + String(SERVER_URL));
  Serial.println("   - Categoría: " + CATEGORIA);
  Serial.println("   - Botón: GPIO" + String(BUTTON_PIN));
  Serial.println("   - LED: GPIO" + String(LED_PIN));
  Serial.println();
  Serial.println("🎯 Instrucciones:");
  Serial.println("   1. Presiona el botón BOOT para enviar tiempo");
  Serial.println("   2. Escribe comandos por Serial:");
  Serial.println("      - 'test' = enviar tiempo aleatorio");
  Serial.println("      - 'velocista' o 'rally' = cambiar categoría");
  Serial.println("      - 'status' = ver estado");
  Serial.println();
  Serial.println("✅ Sistema listo!");
  Serial.println("===========================================");
}

// ==================== LOOP PRINCIPAL ====================
void loop() {
  // Verificar botón
  verificarBoton();
  
  // Verificar comandos por serial
  verificarSerial();
  
  delay(50);  // Pequeña pausa para estabilidad
}

// ==================== FUNCIONES WiFi ====================
void conectarWiFi() {
  Serial.print("📡 Conectando a WiFi '" + String(WIFI_SSID) + "'");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 30) {
    delay(500);
    Serial.print(".");
    intentos++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi conectado exitosamente!");
    Serial.println("📍 IP local: " + WiFi.localIP().toString());
    parpadearLED(3, 200);  // 3 parpadeos lentos = conexión exitosa
  } else {
    Serial.println();
    Serial.println("❌ Error: No se pudo conectar a WiFi");
    Serial.println("   Verifica SSID y contraseña");
    parpadearLED(10, 100); // 10 parpadeos rápidos = error
  }
}

// ==================== FUNCIONES DE BOTÓN ====================
void verificarBoton() {
  if (digitalRead(BUTTON_PIN) == LOW) {  // Botón presionado (pull-up)
    unsigned long currentTime = millis();
    
    if (currentTime - lastButtonTime > DEBOUNCE_DELAY) {
      lastButtonTime = currentTime;
      
      // Generar tiempo aleatorio para demostración
      float tiempo = generarTiempoAleatorio();
      
      Serial.println();
      Serial.println("🔘 Botón presionado - Enviando tiempo...");
      enviarTiempo(tiempo, CATEGORIA);
    }
  }
}

// ==================== FUNCIONES DE SERIAL ====================
void verificarSerial() {
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    comando.toLowerCase();
    
    Serial.println();
    Serial.println("📝 Comando recibido: '" + comando + "'");
    
    if (comando == "test") {
      float tiempo = generarTiempoAleatorio();
      Serial.println("🧪 Enviando tiempo de prueba: " + String(tiempo, 5) + "s");
      enviarTiempo(tiempo, CATEGORIA);
      
    } else if (comando == "velocista" || comando == "rally") {
      // Cambiar categoría (nota: esto requeriría modificar CATEGORIA como variable)
      Serial.println("📂 Categoría solicitada: " + comando);
      Serial.println("   (Para cambiar categoría, modifica el código y recompila)");
      
    } else if (comando == "status") {
      mostrarStatus();
      
    } else if (comando == "help" || comando == "ayuda") {
      mostrarAyuda();
      
    } else {
      Serial.println("❓ Comando desconocido. Escribe 'help' para ver comandos disponibles.");
    }
  }
}

// ==================== FUNCIÓN PRINCIPAL DE ENVÍO ====================
void enviarTiempo(float tiempo, String categoria) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ Error: WiFi desconectado");
    parpadearLED(5, 100);
    return;
  }
  
  Serial.println("📤 Preparando envío...");
  Serial.println("   📊 Tiempo: " + String(tiempo, 5) + "s");
  Serial.println("   📂 Categoría: " + categoria);
  Serial.println("   🌐 URL: " + String(SERVER_URL));
  
  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000);  // 10 segundos timeout
  
  // Crear JSON
  StaticJsonDocument<200> doc;
  doc["categoria"] = categoria;
  doc["tiempo"] = String(tiempo, 5);  // 5 decimales de precisión
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("   📋 JSON: " + jsonString);
  
  // Indicar envío en progreso
  digitalWrite(LED_PIN, HIGH);
  
  // Enviar POST request
  Serial.println("📡 Enviando datos...");
  int httpResponseCode = http.POST(jsonString);
  
  digitalWrite(LED_PIN, LOW);
  
  // Procesar respuesta
  if (httpResponseCode > 0) {
    String response = http.getString();
    
    Serial.println("📨 Respuesta del servidor:");
    Serial.println("   📊 Código: " + String(httpResponseCode));
    Serial.println("   📄 Contenido: " + response);
    
    if (httpResponseCode == 200) {
      Serial.println("✅ ¡Tiempo registrado exitosamente!");
      parpadearLED(3, 300);  // 3 parpadeos lentos = éxito
    } else if (httpResponseCode == 400) {
      Serial.println("⚠️  Error 400: Verifica que haya una sesión activa esperando");
      parpadearLED(5, 200);  // 5 parpadeos medianos = error 400
    } else {
      Serial.println("❌ Error del servidor");
      parpadearLED(7, 150);  // 7 parpadeos = error servidor
    }
  } else {
    Serial.println("❌ Error de conexión HTTP:");
    Serial.println("   Código: " + String(httpResponseCode));
    Serial.println("   Posibles causas:");
    Serial.println("   - Servidor Django no está ejecutándose");
    Serial.println("   - IP incorrecta en SERVER_URL");
    Serial.println("   - Problemas de red");
    parpadearLED(10, 100);  // 10 parpadeos rápidos = error conexión
  }
  
  http.end();
  Serial.println("===========================================");
}

// ==================== FUNCIONES AUXILIARES ====================
float generarTiempoAleatorio() {
  // Generar tiempo aleatorio según la categoría
  if (CATEGORIA == "velocista") {
    // Velocista: entre 8.00 y 20.00 segundos
    return random(800, 2000) / 100.0;
  } else {
    // Rally: entre 20.00 y 50.00 segundos
    return random(2000, 5000) / 100.0;
  }
}

void parpadearLED(int veces, int duracion) {
  for (int i = 0; i < veces; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(duracion);
    digitalWrite(LED_PIN, LOW);
    delay(duracion);
  }
}

void mostrarStatus() {
  Serial.println("📊 Estado del Sistema:");
  Serial.println("   🌐 WiFi: " + String(WiFi.status() == WL_CONNECTED ? "Conectado" : "Desconectado"));
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("   📍 IP: " + WiFi.localIP().toString());
    Serial.println("   📶 RSSI: " + String(WiFi.RSSI()) + " dBm");
  }
  Serial.println("   🎯 Servidor: " + String(SERVER_URL));
  Serial.println("   📂 Categoría: " + CATEGORIA);
  Serial.println("   💾 Memoria libre: " + String(ESP.getFreeHeap()) + " bytes");
  Serial.println("   ⏰ Uptime: " + String(millis() / 1000) + " segundos");
}

void mostrarAyuda() {
  Serial.println("📖 Comandos Disponibles:");
  Serial.println("   🧪 'test'      - Enviar tiempo aleatorio de prueba");
  Serial.println("   📊 'status'    - Mostrar estado del sistema");
  Serial.println("   📖 'help'      - Mostrar esta ayuda");
  Serial.println("   🔘 Botón BOOT  - Enviar tiempo aleatorio");
  Serial.println();
  Serial.println("🔧 Configuración Actual:");
  Serial.println("   📂 Categoría: " + CATEGORIA);
  Serial.println("   🌐 Servidor: " + String(SERVER_URL));
}

/*
 * ==================== INSTRUCCIONES DE USO ====================
 * 
 * 1. CONFIGURACIÓN INICIAL:
 *    - Cambia WIFI_SSID y WIFI_PASSWORD por tus credenciales
 *    - Verifica que SERVER_URL tenga la IP correcta del servidor Django
 *    - Cambia CATEGORIA si necesitas "rally" en lugar de "velocista"
 * 
 * 2. LIBRERÍAS REQUERIDAS:
 *    - ArduinoJson (instalar desde Library Manager)
 *    - WiFi (incluida en ESP32 Core)
 *    - HTTPClient (incluida en ESP32 Core)
 * 
 * 3. HARDWARE:
 *    - ESP32 (cualquier modelo)
 *    - LED integrado en GPIO2 (opcional, para indicaciones visuales)
 *    - Botón BOOT (GPIO0) para envío manual
 * 
 * 4. FUNCIONAMIENTO:
 *    - Al iniciar, se conecta automáticamente a WiFi
 *    - Presiona el botón BOOT para enviar un tiempo aleatorio
 *    - Usa comandos por Serial Monitor para pruebas
 * 
 * 5. INDICACIONES LED:
 *    - 3 parpadeos lentos: Conexión WiFi exitosa / Tiempo enviado OK
 *    - 5 parpadeos medianos: Error 400 (no hay sesión activa)
 *    - 7 parpadeos: Error del servidor
 *    - 10 parpadeos rápidos: Error de conexión
 * 
 * 6. SOLUCIÓN DE PROBLEMAS:
 *    - Si no conecta WiFi: verifica SSID y contraseña
 *    - Si error 400: asegúrate de tener sesión activa en el web
 *    - Si error conexión: verifica que el servidor Django esté corriendo
 *    - Usa 'status' para verificar el estado del sistema
 * 
 * ==================== NOTAS IMPORTANTES ====================
 * 
 * - ASEGÚRATE de que el servidor Django esté ejecutándose
 * - DEBE haber una sesión activa esperando en el sistema web
 * - Solo funciona con categorías "velocista" y "rally"
 * - El formato del tiempo debe ser string con decimales
 * 
 */
