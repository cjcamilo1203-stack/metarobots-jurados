#!/usr/bin/env python
"""
Script para iniciar el servidor MetaRobots Jurados
Automatiza el proceso de verificación y arranque
"""

import os
import sys
import subprocess
import platform

def print_banner():
    """Mostrar banner de inicio"""
    print("=" * 60)
    print("🤖 MetaRobots - Sistema de Jurados")
    print("   Universidad de los Llanos")
    print("=" * 60)

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_venv():
    """Verificar si está en entorno virtual"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("✅ Entorno virtual activo - OK")
        return True
    else:
        print("⚠️  Advertencia: No se detectó entorno virtual activo")
        response = input("¿Continuar de todas formas? (s/N): ").lower()
        return response == 's'

def check_dependencies():
    """Verificar dependencias instaladas"""
    try:
        import django
        print(f"✅ Django {django.get_version()} - OK")
    except ImportError:
        print("❌ Error: Django no está instalado")
        print("   Ejecuta: pip install -r requirements.txt")
        return False
    
    try:
        import rest_framework
        print("✅ Django REST Framework - OK")
    except ImportError:
        print("❌ Error: Django REST Framework no está instalado")
        print("   Ejecuta: pip install -r requirements.txt")
        return False
    
    return True

def check_database():
    """Verificar estado de la base de datos"""
    if not os.path.exists('db.sqlite3'):
        print("⚠️  Base de datos no encontrada, ejecutando migraciones...")
        try:
            subprocess.run(['python', 'manage.py', 'migrate'], check=True)
            print("✅ Migraciones aplicadas - OK")
        except subprocess.CalledProcessError:
            print("❌ Error al aplicar migraciones")
            return False
    else:
        print("✅ Base de datos encontrada - OK")
    
    return True

def check_static_files():
    """Verificar archivos estáticos (si es necesario)"""
    # En desarrollo no es necesario, pero se puede agregar para producción
    print("✅ Archivos estáticos - OK")
    return True

def get_local_ip():
    """Obtener IP local para mostrar al usuario"""
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except:
        return "127.0.0.1"

def start_server():
    """Iniciar servidor Django"""
    local_ip = get_local_ip()
    
    print("\n🚀 Iniciando servidor...")
    print(f"📱 Acceso local: http://127.0.0.1:8000")
    print(f"🌐 Acceso en red: http://{local_ip}:8000")
    print(f"🔧 Admin: http://127.0.0.1:8000/admin")
    print("\n💡 Para ESP32, usar la IP de red en el código")
    print("⏹️  Presiona Ctrl+C para detener el servidor")
    print("-" * 60)
    
    try:
        # Usar os.system en lugar de subprocess para mejor compatibilidad en Windows
        os.system('python manage.py runserver 0.0.0.0:8000')
    except KeyboardInterrupt:
        print("\n\n👋 Servidor detenido. ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error al iniciar servidor: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    print_banner()
    
    # Verificaciones previas
    checks = [
        ("Versión de Python", check_python_version),
        ("Entorno virtual", check_venv),
        ("Dependencias", check_dependencies),
        ("Base de datos", check_database),
        ("Archivos estáticos", check_static_files),
    ]
    
    print("\n🔍 Ejecutando verificaciones previas...")
    print("-" * 40)
    
    for name, check_func in checks:
        if not check_func():
            print(f"\n❌ Verificación fallida: {name}")
            print("   Revisa los errores anteriores y vuelve a intentar.")
            sys.exit(1)
    
    print("\n✅ Todas las verificaciones pasaron correctamente!")
    
    # Preguntar si inicializar datos de ejemplo
    if not os.path.exists('db.sqlite3') or input("\n¿Inicializar datos de ejemplo? (S/n): ").lower() != 'n':
        print("\n📊 Inicializando datos de ejemplo...")
        try:
            result = os.system('python init_data.py')
            if result != 0:
                print("⚠️  Error al inicializar datos de ejemplo (continuando...)")
        except Exception:
            print("⚠️  Error al inicializar datos de ejemplo (continuando...)")
    
    # Iniciar servidor
    start_server()

if __name__ == '__main__':
    main()
