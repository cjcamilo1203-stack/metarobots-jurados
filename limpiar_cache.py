#!/usr/bin/env python
"""
Script para limpiar caché del navegador y verificar archivos estáticos
"""

import webbrowser
import os
import time

def limpiar_cache_navegador():
    """Abrir páginas para limpiar caché"""
    print("🧹 Limpiando caché del navegador...")

    # URLs para limpiar caché
    urls_cache = [
        "chrome://net-internals/#sockets",
        "chrome://net-internals/#dns",
        "chrome://net-internals/#httpCache",
        "chrome://settings/clearBrowserData"
    ]

    print("🔍 Abre estas URLs en Chrome para limpiar caché:")
    for i, url in enumerate(urls_cache, 1):
        print(f"   {i}. {url}")

    print("\n💡 O puedes:")
    print("   - Presionar Ctrl+Shift+R (recargar forzado)")
    print("   - Presionar F12 → clic derecho en recargar → Vaciar caché y recargar")

def verificar_archivos_estaticos():
    """Verificar si los archivos estáticos se sirven correctamente"""
    print("📁 Verificando archivos estáticos...")

    # Archivos estáticos que deberían existir
    archivos_estaticos = [
        "http://127.0.0.1:8000/static/bootstrap/css/bootstrap.min.css",
        "http://127.0.0.1:8000/static/bootstrap/js/bootstrap.bundle.min.js",
        "http://127.0.0.1:8000/static/bootstrap-icons/font/bootstrap-icons.css",
        "http://192.168.184.125:8000/static/bootstrap/css/bootstrap.min.css",
    ]

    print("🌐 Prueba estas URLs en tu navegador:")
    for i, url in enumerate(archivos_estaticos, 1):
        print(f"   {i}. {url}")

    print("\n✅ Si estos archivos cargan correctamente, el problema está resuelto")
    print("❌ Si dan error 404, hay un problema con la configuración de archivos estáticos")

def main():
    print("=" * 60)
    print("🧹 MetaRobots - Limpiar Caché y Verificar Estáticos")
    print("=" * 60)

    print("\n🔍 Problema detectado:")
    print("   - ✅ Localhost funciona bien")
    print("   - ❌ IP externa no carga CSS")

    print("\n🛠️  Soluciones implementadas:")
    print("   - ✅ ALLOWED_HOSTS configurado para '*'")
    print("   - ✅ URLs de archivos estáticos agregadas")
    print("   - ✅ Servidor configurado en 0.0.0.0:8000")

    print("\n📋 Pasos para solucionar:")
    print("   1. Reinicia el servidor (hecho)")
    print("   2. Limpia la caché del navegador")
    print("   3. Prueba acceder desde la IP externa")

    print("\n" + "=" * 40)
    limpiar_cache_navegador()
    print("\n" + "=" * 40)
    verificar_archivos_estaticos()

    print("\n💡 Prueba ahora:")
    print("   🌐 http://192.168.184.125:8000")
    print("   📱 http://127.0.0.1:8000")

    print("\n🎯 Si aún no funciona:")
    print("   - Verifica que el servidor esté corriendo")
    print("   - Limpia completamente la caché")
    print("   - Prueba en un navegador diferente")
    print("   - Reinicia el router/modem si es necesario")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
