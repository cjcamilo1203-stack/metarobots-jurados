from django.urls import path
from . import views

app_name = 'jurados'

urlpatterns = [
    # Vistas principales
    path('', views.home, name='home'),
    path('categoria/<str:categoria_nombre>/', views.categoria_detalle, name='categoria_detalle'),
    path('robot/<int:robot_id>/', views.robot_detalle, name='robot_detalle'),
    
    # CRUD de robots
    path('categoria/<str:categoria_nombre>/agregar-robot/', views.agregar_robot, name='agregar_robot'),
    path('categoria/<str:categoria_nombre>/editar-robot/<int:robot_id>/', views.editar_robot, name='editar_robot'),
    path('categoria/<str:categoria_nombre>/eliminar-robot/<int:robot_id>/', views.eliminar_robot, name='eliminar_robot'),
    
    # Gestión de sesiones de registro
    path('robot/<int:robot_id>/iniciar-sesion/', views.iniciar_sesion, name='iniciar_sesion'),
    path('robot/<int:robot_id>/finalizar-sesion/', views.finalizar_sesion, name='finalizar_sesion'),
    
    # Gestión de tiempos
    path('robot/<int:robot_id>/agregar-tiempo-manual/', views.agregar_tiempo_manual, name='agregar_tiempo_manual'),
    path('robot/<int:robot_id>/editar-tiempo/<int:tiempo_id>/', views.editar_tiempo, name='editar_tiempo'),
    path('robot/<int:robot_id>/eliminar-tiempo/<int:tiempo_id>/', views.eliminar_tiempo, name='eliminar_tiempo'),
    
    # Utilidades
    path('robot/<int:robot_id>/check-new-times/', views.check_new_times, name='check_new_times'),
    
    # API para ESP32
    path('api/registrar-tiempo/', views.api_registrar_tiempo, name='api_registrar_tiempo'),
]
