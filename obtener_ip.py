#!/usr/bin/env python
"""
Script para obtener la IP local del servidor
Útil para configurar la ESP32 con la IP correcta
"""

import socket
import subprocess
import sys

def obtener_ip_local():
    """Obtener IP local del sistema"""
    try:
        # Método 1: Conectar a un servidor externo para obtener la IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
        return ip_local
    except:
        try:
            # Método 2: Usar hostname
            hostname = socket.gethostname()
            ip_local = socket.gethostbyname(hostname)
            return ip_local
        except:
            return "127.0.0.1"

def obtener_todas_las_ips():
    """Obtener todas las interfaces de red disponibles"""
    ips = []
    try:
        # En Windows
        if sys.platform == "win32":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if 'IPv4' in line and '192.168.' in line:
                    ip = line.split(':')[1].strip()
                    if ip not in ips:
                        ips.append(ip)
        else:
            # En Linux/Mac
            result = subprocess.run(['ifconfig'], capture_output=True, text=True, shell=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if 'inet ' in line and '192.168.' in line:
                    ip = line.split()[1]
                    if ip not in ips:
                        ips.append(ip)
    except:
        pass
    
    return ips

def main():
    print("=" * 60)
    print("🌐 MetaRobots - Obtener IP del Servidor")
    print("=" * 60)
    
    # IP principal
    ip_principal = obtener_ip_local()
    print(f"📍 IP Principal: {ip_principal}")
    
    # Todas las IPs
    todas_ips = obtener_todas_las_ips()
    if todas_ips:
        print("\n📋 Todas las IPs disponibles:")
        for i, ip in enumerate(todas_ips, 1):
            print(f"   {i}. {ip}")
    
    print(f"\n🔧 Para ESP32, usa esta configuración:")
    print(f'const char* serverURL = "http://{ip_principal}:8000/api/registrar-tiempo/";')
    
    print(f"\n🌐 URLs de acceso:")
    print(f"   📱 Local: http://127.0.0.1:8000")
    print(f"   🌍 Red: http://{ip_principal}:8000")
    print(f"   🔧 Admin: http://{ip_principal}:8000/admin")
    
    print(f"\n💡 Notas:")
    print(f"   - Asegúrate de que Django esté ejecutándose con: python manage.py runserver 0.0.0.0:8000")
    print(f"   - La ESP32 debe estar en la misma red WiFi")
    print(f"   - ALLOWED_HOSTS está configurado para aceptar cualquier IP")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
