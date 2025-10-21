from django.urls import path
from . import views

app_name = 'jurados'

urlpatterns = [
    # Vistas principales
    path('', views.home, name='home'),
    path('rally/tiempos/', views.tiempos_rally, name='tiempos_rally'),
    path('rally/llaves-top12/', views.rally_llaves_top12, name='rally_llaves_top12'),
    path('rally/crear-torneo-top12/', views.rally_crear_torneo_top12, name='rally_crear_torneo_top12'),
    path('rally/triadas/<int:torneo_id>/', views.rally_triadas, name='rally_triadas'),
    path('rally/triadas/<int:torneo_id>/winner/<int:triad_id>/<int:winner_id>/', views.rally_triada_winner, name='rally_triada_winner'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/rally/', views.dashboard_rally, name='dashboard_rally'),
    path('dashboard/rally/<int:torneo_id>/', views.dashboard_rally, name='dashboard_rally_id'),
    path('torneos/', views.torneos_app, name='torneos_app'),
    # Torneos integrados (poner primero rutas con IDs para evitar colisiones)
    path('torneos/<int:torneo_id>/', views.torneo_detalle, name='torneo_detalle'),
    path('torneos/<int:torneo_id>/ver-llaves/', views.torneo_ver_llaves, name='torneo_ver_llaves'),
    path('torneos/<int:torneo_id>/guardar-ganador/<int:match_id>/', views.torneo_guardar_ganador, name='torneo_guardar_ganador'),
    path('torneos/categoria/<str:categoria>/', views.torneo_categoria, name='torneo_categoria'),
    path('torneos/categoria/<str:categoria>/reiniciar/', views.torneo_reiniciar, name='torneo_reiniciar'),
    path('torneos/categoria/<str:categoria>/nuevo/', views.torneo_nuevo, name='torneo_nuevo'),
    path('torneos/<int:torneo_id>/marcar-ganador/<int:match_id>/<int:winner_participant_id>/', views.torneo_marcar_ganador, name='torneo_marcar_ganador'),
    path('futbol/<int:torneo_id>/', views.futbol_grupos, name='futbol_grupos'),
    path('futbol/<int:torneo_id>/resultado/<int:match_id>/', views.futbol_registrar_resultado, name='futbol_registrar_resultado'),
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
