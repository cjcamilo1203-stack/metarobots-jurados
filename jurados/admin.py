from django.contrib import admin
from .models import Categoria, Robot, SesionRegistro, TiempoRegistro

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa', 'fecha_creacion']
    list_filter = ['activa', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']

@admin.register(Robot)
class RobotAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'autor_principal', 'autor_secundario', 'activo', 'fecha_registro']
    list_filter = ['categoria', 'activo', 'fecha_registro']
    search_fields = ['nombre', 'autor_principal', 'autor_secundario']
    ordering = ['categoria', 'nombre']

@admin.register(SesionRegistro)
class SesionRegistroAdmin(admin.ModelAdmin):
    list_display = ['robot', 'activa', 'usuario', 'fecha_inicio', 'fecha_fin']
    list_filter = ['activa', 'fecha_inicio', 'robot__categoria']
    search_fields = ['robot__nombre', 'usuario']
    ordering = ['-fecha_inicio']

@admin.register(TiempoRegistro)
class TiempoRegistroAdmin(admin.ModelAdmin):
    list_display = ['robot', 'tiempo', 'metodo_registro', 'valido', 'fecha_registro']
    list_filter = ['metodo_registro', 'valido', 'fecha_registro', 'robot__categoria']
    search_fields = ['robot__nombre', 'observaciones']
    ordering = ['-fecha_registro']
