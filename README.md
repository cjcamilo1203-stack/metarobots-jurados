# 🤖 MetaRobots - Sistema de Jurados

Sistema web desarrollado en Django para la gestión de competencias de robots, específicamente diseñado para las categorías **Velocista** y **Rally RC**. Permite registrar robots, gestionar tiempos tanto manualmente como a través de una API para ESP32, y visualizar rankings en tiempo real.

## 🚀 Características Principales

### 🏆 Gestión de Competencias

- **6 Categorías disponibles**: Rally, Fútbol, Sumo RC, Sumo Autónomo, Barcos, Velocista
- **Funcionales actualmente**: Rally y Velocista
- Interfaz intuitiva para selección de categorías

### 🤖 Gestión de Robots

- **CRUD completo** de robots por categoría
- Registro de **autor principal** (obligatorio) y **autor secundario** (opcional)
- Validación de nombres únicos por categoría
- Eliminación suave (soft delete)

### ⏱️ Sistema de Registro de Tiempos

- **Registro automático** desde ESP32 mediante API REST
- **Registro manual** por parte del jurado
- **Sistema de sesiones** - solo registra tiempos cuando hay una sesión activa
- **Validación de categoría** - solo acepta tiempos de la categoría correcta
- Edición y eliminación de tiempos registrados
- Marcado de tiempos como válidos/inválidos

### 📊 Dashboard y Rankings

- **Ranking automático** por mejor tiempo
- **Visualización en tiempo real** de posiciones
- **Historial completo** de tiempos por robot
- **Auto-refresh** cuando hay sesión activa

### 🔌 API REST para ESP32

- Endpoint: `POST /api/registrar-tiempo/`
- Formato JSON requerido:

```json
{
  "categoria": "velocista", // o "rally"
  "tiempo": "45.12341" // tiempo en segundos
}
```

## 🛠️ Instalación y Configuración

### Prerrequisitos

- Python 3.8+
- pip (gestor de paquetes de Python)

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd metarobots-jurados
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Aplicar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario (opcional)

```bash
python manage.py createsuperuser
```

### 7. Inicializar datos de ejemplo

```bash
python init_data.py
```

### 8. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

El sistema estará disponible en: **http://127.0.0.1:8000**

## 🎮 Uso del Sistema

### Para Jurados

1. **Seleccionar Categoría**: Desde la página principal, elegir entre Rally o Velocista
2. **Gestionar Robots**:
   - Agregar nuevos robots con nombre y autores
   - Editar información de robots existentes
   - Ver historial de tiempos por robot
3. **Registrar Tiempos**:
   - Hacer clic en "Registrar Tiempo" para activar sesión
   - El sistema quedará esperando datos de la ESP32
   - También se pueden agregar tiempos manualmente
4. **Ver Rankings**: Los robots se ordenan automáticamente por mejor tiempo

### Para ESP32

Enviar petición POST a `http://ip-del-servidor:8000/api/registrar-tiempo/` con:

```json
{
  "categoria": "velocista",
  "tiempo": "12.34567"
}
```

**Respuestas posibles:**

- ✅ **200 OK**: Tiempo registrado correctamente
- ❌ **400 Bad Request**: Error en datos o no hay sesión activa
- ❌ **500 Internal Server Error**: Error interno del servidor

## 🏗️ Arquitectura del Sistema

### Modelos de Datos

- **Categoria**: Gestión de las 6 categorías de competencia
- **Robot**: Información de robots participantes
- **SesionRegistro**: Control de sesiones activas para registro
- **TiempoRegistro**: Almacenamiento de todos los tiempos registrados

### Flujo de Registro de Tiempos

1. Jurado selecciona robot y activa "Registrar Tiempo"
2. Se crea una **SesionRegistro** activa
3. ESP32 envía tiempo via API
4. Sistema valida categoría y sesión activa
5. Se registra el tiempo y se finaliza la sesión
6. Se actualiza automáticamente el ranking

## 🔧 Configuración Técnica

### Base de Datos

- **SQLite3** por defecto (incluida con Python)
- Configuración en `settings.py`
- Migraciones automáticas con Django

### API REST

- **Django REST Framework**
- Endpoint sin autenticación para ESP32
- Validación de datos JSON
- Manejo de errores robusto

### Frontend

- **Bootstrap 5** para UI responsiva
- **JavaScript vanilla** para interactividad
- **Auto-refresh** en páginas de robots activos
- **Modales** para formularios

## 🐛 Solución de Problemas

### Error: "No hay sesión activa"

- Verificar que se haya presionado "Registrar Tiempo"
- Solo una sesión puede estar activa por categoría

### Error: "Categoría no válida"

- Verificar que la ESP32 envíe "velocista" o "rally" (en minúsculas)

### Tiempos no aparecen

- Verificar que la sesión esté activa
- Revisar logs del servidor Django
- Verificar formato JSON de la ESP32

## 📝 Próximas Funcionalidades

- [ ] Implementar categorías Fútbol, Sumo RC, Sumo Autónomo, Barcos
- [ ] Sistema de autenticación para jurados
- [ ] Exportación de resultados a PDF/Excel
- [ ] Notificaciones en tiempo real
- [ ] Configuración de parámetros de competencia

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

**Desarrollado para MetaRobots - Universidad de los Llanos** 🎓
Plataforma de seguimiento a categorías de competencia robotica.
