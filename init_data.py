#!/usr/bin/env python
"""
Script para inicializar datos de ejemplo en el sistema MetaRobots Jurados
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metarobots_jurados.settings')
django.setup()

from jurados.models import Categoria, Robot, TiempoRegistro

def init_data():
    """Inicializar datos de ejemplo"""
    print("🤖 Inicializando datos de ejemplo para MetaRobots Jurados...")
    
    # Crear categorías
    categoria_velocista, created = Categoria.objects.get_or_create(
        nombre='velocista',
        defaults={'descripcion': 'Competencia de velocidad en línea recta', 'activa': True}
    )
    if created:
        print("✅ Categoría 'Velocista' creada")
    
    categoria_rally, created = Categoria.objects.get_or_create(
        nombre='rally',
        defaults={'descripcion': 'Competencia de habilidad y velocidad', 'activa': True}
    )
    if created:
        print("✅ Categoría 'Rally' creada")
    
    # Robots para Velocista
    robots_velocista = [
        {'nombre': 'Lightning McQueen', 'autor_principal': 'Juan Pérez', 'autor_secundario': 'María García'},
        {'nombre': 'Speed Demon', 'autor_principal': 'Carlos Rodríguez', 'autor_secundario': None},
        {'nombre': 'Turbo Boost', 'autor_principal': 'Ana López', 'autor_secundario': 'Luis Martínez'},
        {'nombre': 'Flash Runner', 'autor_principal': 'Pedro Sánchez', 'autor_secundario': None},
    ]
    
    for robot_data in robots_velocista:
        robot, created = Robot.objects.get_or_create(
            categoria=categoria_velocista,
            nombre=robot_data['nombre'],
            defaults={
                'autor_principal': robot_data['autor_principal'],
                'autor_secundario': robot_data['autor_secundario'],
                'activo': True
            }
        )
        if created:
            print(f"🤖 Robot '{robot.nombre}' creado para Velocista")
            
            # Agregar algunos tiempos de ejemplo
            tiempos_ejemplo = [
                Decimal('12.345'),
                Decimal('11.892'),
                Decimal('13.156'),
                Decimal('12.001'),
            ]
            
            for i, tiempo in enumerate(tiempos_ejemplo):
                TiempoRegistro.objects.create(
                    robot=robot,
                    tiempo=tiempo,
                    metodo_registro='manual' if i % 2 == 0 else 'esp32',
                    valido=True,
                    observaciones=f'Tiempo de prueba #{i+1}'
                )
            print(f"   ⏱️  Agregados {len(tiempos_ejemplo)} tiempos de ejemplo")
    
    # Robots para Rally
    robots_rally = [
        {'nombre': 'Rally Master', 'autor_principal': 'Diego Fernández', 'autor_secundario': 'Sofia Herrera'},
        {'nombre': 'Off-Road King', 'autor_principal': 'Miguel Torres', 'autor_secundario': None},
        {'nombre': 'Dirt Crusher', 'autor_principal': 'Valentina Castro', 'autor_secundario': 'Andrés Morales'},
    ]
    
    for robot_data in robots_rally:
        robot, created = Robot.objects.get_or_create(
            categoria=categoria_rally,
            nombre=robot_data['nombre'],
            defaults={
                'autor_principal': robot_data['autor_principal'],
                'autor_secundario': robot_data['autor_secundario'],
                'activo': True
            }
        )
        if created:
            print(f"🏁 Robot '{robot.nombre}' creado para Rally")
            
            # Agregar algunos tiempos de ejemplo para rally (generalmente más altos)
            tiempos_ejemplo = [
                Decimal('25.678'),
                Decimal('24.123'),
                Decimal('26.789'),
                Decimal('23.456'),
            ]
            
            for i, tiempo in enumerate(tiempos_ejemplo):
                TiempoRegistro.objects.create(
                    robot=robot,
                    tiempo=tiempo,
                    metodo_registro='manual' if i % 2 == 0 else 'esp32',
                    valido=True,
                    observaciones=f'Tiempo de prueba rally #{i+1}'
                )
            print(f"   ⏱️  Agregados {len(tiempos_ejemplo)} tiempos de ejemplo")
    
    print("\n🎉 ¡Datos de ejemplo inicializados correctamente!")
    print("\n📋 Resumen:")
    print(f"   - Categorías: {Categoria.objects.count()}")
    print(f"   - Robots: {Robot.objects.filter(activo=True).count()}")
    print(f"   - Tiempos registrados: {TiempoRegistro.objects.count()}")
    
    print("\n🌐 Puedes acceder al sistema en: http://127.0.0.1:8000")
    print("🔧 Panel de administración en: http://127.0.0.1:8000/admin")

if __name__ == '__main__':
    init_data()
