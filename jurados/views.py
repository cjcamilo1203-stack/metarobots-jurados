from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
import json
from decimal import Decimal

from .models import Categoria, Robot, SesionRegistro, TiempoRegistro

def home(request):
    """Vista principal con selección de categorías"""
    return render(request, 'jurados/home.html')

def categoria_detalle(request, categoria_nombre):
    """Vista de detalle de una categoría específica"""
    if categoria_nombre not in ['rally', 'velocista']:
        messages.error(request, 'Esta categoría no está disponible aún.')
        return redirect('jurados:home')
    
    categoria, created = Categoria.objects.get_or_create(
        nombre=categoria_nombre,
        defaults={'activa': True}
    )
    
    robots = Robot.objects.filter(categoria=categoria, activo=True).order_by('nombre')
    
    # Crear ranking basado en mejor tiempo
    ranking = []
    for robot in robots:
        mejor_tiempo = robot.mejor_tiempo()
        if mejor_tiempo:
            ranking.append({
                'robot': robot,
                'mejor_tiempo': mejor_tiempo,
                'nombre': robot.nombre,
                'autor_principal': robot.autor_principal,
                'autor_secundario': robot.autor_secundario,
            })
    
    ranking.sort(key=lambda x: x['mejor_tiempo'])
    
    context = {
        'categoria': categoria,
        'robots': robots,
        'ranking': ranking,
    }
    return render(request, 'jurados/categoria_detalle.html', context)

def robot_detalle(request, robot_id):
    """Vista de detalle de un robot específico"""
    robot = get_object_or_404(Robot, id=robot_id, activo=True)
    tiempos = TiempoRegistro.objects.filter(robot=robot).order_by('-fecha_registro')
    sesion_activa = SesionRegistro.objects.filter(robot=robot, activa=True).first()
    
    context = {
        'robot': robot,
        'tiempos': tiempos,
        'sesion_activa': sesion_activa,
    }
    return render(request, 'jurados/robot_detalle.html', context)

@require_http_methods(["POST"])
def agregar_robot(request, categoria_nombre):
    """Agregar un nuevo robot a una categoría"""
    categoria = get_object_or_404(Categoria, nombre=categoria_nombre)
    
    nombre = request.POST.get('nombre', '').strip()
    autor_principal = request.POST.get('autor_principal', '').strip()
    autor_secundario = request.POST.get('autor_secundario', '').strip()
    
    if not nombre or not autor_principal:
        messages.error(request, 'El nombre del robot y el autor principal son obligatorios.')
        return redirect('jurados:categoria_detalle', categoria_nombre=categoria_nombre)
    
    # Verificar que no existe un robot con el mismo nombre en la categoría
    if Robot.objects.filter(categoria=categoria, nombre=nombre, activo=True).exists():
        messages.error(request, f'Ya existe un robot con el nombre "{nombre}" en esta categoría.')
        return redirect('jurados:categoria_detalle', categoria_nombre=categoria_nombre)
    
    robot = Robot.objects.create(
        categoria=categoria,
        nombre=nombre,
        autor_principal=autor_principal,
        autor_secundario=autor_secundario if autor_secundario else None,
    )
    
    messages.success(request, f'Robot "{nombre}" agregado exitosamente.')
    return redirect('jurados:categoria_detalle', categoria_nombre=categoria_nombre)

@require_http_methods(["POST"])
def editar_robot(request, categoria_nombre, robot_id):
    """Editar un robot existente"""
    robot = get_object_or_404(Robot, id=robot_id, activo=True)
    
    nombre = request.POST.get('nombre', '').strip()
    autor_principal = request.POST.get('autor_principal', '').strip()
    autor_secundario = request.POST.get('autor_secundario', '').strip()
    
    if not nombre or not autor_principal:
        messages.error(request, 'El nombre del robot y el autor principal son obligatorios.')
        return redirect('jurados:categoria_detalle', categoria_nombre=categoria_nombre)
    
    # Verificar que no existe otro robot con el mismo nombre en la categoría
    if Robot.objects.filter(categoria=robot.categoria, nombre=nombre, activo=True).exclude(id=robot.id).exists():
        messages.error(request, f'Ya existe otro robot con el nombre "{nombre}" en esta categoría.')
        return redirect('jurados:categoria_detalle', categoria_nombre=categoria_nombre)
    
    robot.nombre = nombre
    robot.autor_principal = autor_principal
    robot.autor_secundario = autor_secundario if autor_secundario else None
    robot.save()
    
    messages.success(request, f'Robot "{nombre}" actualizado exitosamente.')
    return redirect('jurados:categoria_detalle', categoria_nombre=categoria_nombre)

@require_http_methods(["POST"])
def eliminar_robot(request, categoria_nombre, robot_id):
    """Eliminar un robot (soft delete)"""
    robot = get_object_or_404(Robot, id=robot_id, activo=True)
    
    robot.activo = False
    robot.save()
    
    messages.success(request, f'Robot "{robot.nombre}" eliminado exitosamente.')
    return redirect('jurados:categoria_detalle', categoria_nombre=categoria_nombre)

@require_http_methods(["POST"])
def iniciar_sesion(request, robot_id):
    """Iniciar sesión de registro de tiempo para un robot"""
    robot = get_object_or_404(Robot, id=robot_id, activo=True)
    
    # Finalizar cualquier sesión activa anterior
    SesionRegistro.objects.filter(robot=robot, activa=True).update(
        activa=False, 
        fecha_fin=timezone.now()
    )
    
    # Crear nueva sesión
    sesion = SesionRegistro.objects.create(
        robot=robot,
        activa=True,
    )
    
    return JsonResponse({'success': True, 'sesion_id': sesion.id})

@require_http_methods(["POST"])
def finalizar_sesion(request, robot_id):
    """Finalizar sesión de registro de tiempo"""
    robot = get_object_or_404(Robot, id=robot_id, activo=True)
    
    sesion = SesionRegistro.objects.filter(robot=robot, activa=True).first()
    if sesion:
        sesion.finalizar()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'No hay sesión activa'})

@require_http_methods(["POST"])
def agregar_tiempo_manual(request, robot_id):
    """Agregar tiempo manual"""
    robot = get_object_or_404(Robot, id=robot_id, activo=True)
    
    try:
        tiempo = Decimal(request.POST.get('tiempo', '0'))
        observaciones = request.POST.get('observaciones', '').strip()
        valido = request.POST.get('valido') == 'on'
        
        if tiempo <= 0:
            messages.error(request, 'El tiempo debe ser mayor a 0.')
            return redirect('jurados:robot_detalle', robot_id=robot_id)
        
        TiempoRegistro.objects.create(
            robot=robot,
            tiempo=tiempo,
            metodo_registro='manual',
            valido=valido,
            observaciones=observaciones,
        )
        
        messages.success(request, f'Tiempo {tiempo}s agregado exitosamente.')
        
    except (ValueError, TypeError):
        messages.error(request, 'Tiempo inválido.')
    
    return redirect('jurados:robot_detalle', robot_id=robot_id)

@require_http_methods(["POST"])
def editar_tiempo(request, robot_id, tiempo_id):
    """Editar tiempo existente"""
    robot = get_object_or_404(Robot, id=robot_id, activo=True)
    tiempo_registro = get_object_or_404(TiempoRegistro, id=tiempo_id, robot=robot)
    
    try:
        nuevo_tiempo = Decimal(request.POST.get('tiempo', '0'))
        observaciones = request.POST.get('observaciones', '').strip()
        valido = request.POST.get('valido') == 'on'
        
        if nuevo_tiempo <= 0:
            messages.error(request, 'El tiempo debe ser mayor a 0.')
            return redirect('jurados:robot_detalle', robot_id=robot_id)
        
        tiempo_registro.tiempo = nuevo_tiempo
        tiempo_registro.observaciones = observaciones
        tiempo_registro.valido = valido
        tiempo_registro.save()
        
        messages.success(request, f'Tiempo actualizado a {nuevo_tiempo}s exitosamente.')
        
    except (ValueError, TypeError):
        messages.error(request, 'Tiempo inválido.')
    
    return redirect('jurados:robot_detalle', robot_id=robot_id)

@require_http_methods(["POST"])
def eliminar_tiempo(request, robot_id, tiempo_id):
    """Eliminar tiempo registrado"""
    robot = get_object_or_404(Robot, id=robot_id, activo=True)
    tiempo_registro = get_object_or_404(TiempoRegistro, id=tiempo_id, robot=robot)
    
    tiempo_valor = tiempo_registro.tiempo
    tiempo_registro.delete()
    
    messages.success(request, f'Tiempo {tiempo_valor}s eliminado exitosamente.')
    return redirect('jurados:robot_detalle', robot_id=robot_id)

def check_new_times(request, robot_id):
    """Verificar si hay nuevos tiempos (para auto-refresh)"""
    robot = get_object_or_404(Robot, id=robot_id, activo=True)
    
    # Verificar si hay tiempos registrados en los últimos 10 segundos
    recent_times = TiempoRegistro.objects.filter(
        robot=robot,
        fecha_registro__gte=timezone.now() - timezone.timedelta(seconds=10)
    ).exists()
    
    return JsonResponse({'has_new_times': recent_times})

@csrf_exempt
@require_http_methods(["POST"])
def api_registrar_tiempo(request):
    """API para recibir tiempos desde ESP32"""
    try:
        data = json.loads(request.body)
        categoria_nombre = data.get('categoria', '').lower()
        tiempo_valor = data.get('tiempo', '')
        
        if categoria_nombre not in ['velocista', 'rally']:
            return JsonResponse({
                'success': False, 
                'error': 'Categoría no válida o no disponible'
            }, status=400)
        
        try:
            tiempo = Decimal(str(tiempo_valor))
            if tiempo <= 0:
                raise ValueError("Tiempo debe ser positivo")
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False, 
                'error': 'Tiempo inválido'
            }, status=400)
        
        # Buscar sesión activa en la categoría
        categoria = Categoria.objects.get(nombre=categoria_nombre)
        sesion_activa = SesionRegistro.objects.filter(
            robot__categoria=categoria,
            activa=True
        ).select_related('robot').first()
        
        if not sesion_activa:
            return JsonResponse({
                'success': False, 
                'error': f'No hay sesión activa esperando tiempo para la categoría {categoria_nombre}'
            }, status=400)
        
        # Registrar el tiempo
        with transaction.atomic():
            tiempo_registro = TiempoRegistro.objects.create(
                robot=sesion_activa.robot,
                tiempo=tiempo,
                metodo_registro='esp32',
                valido=True,
                sesion=sesion_activa,
            )
            
            # Finalizar la sesión
            sesion_activa.finalizar()
        
        return JsonResponse({
            'success': True,
            'robot': sesion_activa.robot.nombre,
            'tiempo': str(tiempo),
            'categoria': categoria_nombre
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'JSON inválido'
        }, status=400)
    except Categoria.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Categoría no encontrada'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error interno: {str(e)}'
        }, status=500)
