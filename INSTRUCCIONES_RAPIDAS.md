# 🚀 Instrucciones Rápidas - MetaRobots Jurados

## ✅ ¡El sistema está listo para usar!

### 🌐 Acceder al Sistema

- **Página principal:** http://127.0.0.1:8000 (o http://192.168.0.122:8000 desde otros dispositivos)
- **Panel de administración:** http://127.0.0.1:8000/admin

### 🎮 Uso Básico

#### 1. **Seleccionar Categoría**

- Ve a la página principal
- Haz clic en **Rally** o **Velocista** (las únicas funcionales)

#### 2. **Gestionar Robots**

- **Agregar:** Botón "Agregar Robot" → Llenar formulario
- **Editar:** Botón "Editar" en cada robot
- **Ver detalles:** Botón "Ver" para acceder al robot específico

#### 3. **Registrar Tiempos**

- Entra al detalle de un robot
- Haz clic en **"Registrar Tiempo"** (botón verde)
- El sistema queda esperando datos de la ESP32
- También puedes agregar tiempos manualmente con "Agregar Tiempo Manual"

#### 4. **Ver Rankings**

- En cada categoría se muestra el ranking automáticamente
- Se ordena por mejor tiempo (menor es mejor)

### 🔌 API para ESP32

**Endpoint:** `POST http://192.168.0.122:8000/api/registrar-tiempo/`

**JSON a enviar:**

```json
{
  "categoria": "velocista",
  "tiempo": "12.34567"
}
```

**Respuestas:**

- ✅ **200:** Tiempo registrado exitosamente
- ❌ **400:** Error en datos o no hay sesión activa
- ❌ **500:** Error interno

### 📊 Datos de Ejemplo Incluidos

El sistema ya tiene datos de prueba:

**Velocista (4 robots):**

- Lightning McQueen - Juan Pérez & María García
- Speed Demon - Carlos Rodríguez
- Turbo Boost - Ana López & Luis Martínez
- Flash Runner - Pedro Sánchez

**Rally (3 robots):**

- Rally Master - Diego Fernández & Sofia Herrera
- Off-Road King - Miguel Torres
- Dirt Crusher - Valentina Castro & Andrés Morales

### 🛠️ Comandos Útiles

```bash
# Iniciar servidor
python manage.py runserver 0.0.0.0:8000

# O usar el script automático
python start_server.py

# Acceder al shell de Django
python manage.py shell

# Ver migraciones
python manage.py showmigrations
```

### 🐛 Solución de Problemas

**Error "No hay sesión activa":**

- Asegúrate de hacer clic en "Registrar Tiempo" antes de enviar desde ESP32
- Solo puede haber una sesión activa por categoría

**ESP32 no puede conectar:**

- Verifica que uses la IP correcta: `192.168.0.122:8000`
- Asegúrate de que ESP32 y servidor están en la misma red

**Tiempos no aparecen:**

- Verifica que la categoría en JSON coincida: "velocista" o "rally"
- Revisa que haya una sesión activa esperando

### 📱 Funcionalidades Principales

✅ **Gestión de categorías** (Rally y Velocista funcionales)  
✅ **CRUD completo de robots** con autores  
✅ **Sistema de sesiones** para control de registro  
✅ **API REST** para ESP32  
✅ **Rankings automáticos** por mejor tiempo  
✅ **Registro manual** de tiempos por jurados  
✅ **Historial completo** de todos los tiempos  
✅ **Interfaz responsive** con Bootstrap 5  
✅ **Auto-refresh** en páginas activas

### 🎯 Próximos Pasos

1. **Configurar ESP32** con el código de ejemplo incluido (`ejemplo_esp32.ino`)
2. **Probar API** enviando datos de prueba
3. **Crear robots** para tus competencias
4. **Registrar tiempos** y ver rankings en tiempo real

---

**¡El sistema está completamente funcional y listo para tu competencia de robots!** 🤖🏆
