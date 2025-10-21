from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.conf import settings
from django.views.decorators.http import require_GET
from django.urls import reverse
import json
from decimal import Decimal

from .models import Categoria, Robot, SesionRegistro, TiempoRegistro
from .models import Tournament, TournamentParticipant, TournamentRound, TournamentMatch, FootballGroup, FootballGroupMatch
from .services_torneo import (
    create_initial_round,
    generate_next_round,
    create_football_groups,
    record_group_result,
    are_all_group_matches_played,
    seed_knockout_from_groups,
    regenerate_following_from,
    create_rally_triads,
    rally_triads_completed,
    seed_semifinals_from_triads,
)

def home(request):
    """Vista principal con selección de categorías"""
    return render(request, 'jurados/home.html')

# Utilidad: permite ingresar tiempos como "mm:ss.sss" o en segundos
def parse_time_input(value: str) -> Decimal:
    try:
        raw = (value or '').strip()
        if not raw:
            return Decimal('0')
        if ':' in raw:
            parts = raw.split(':')
            if len(parts) != 2:
                return Decimal('-1')
            minutes = int(parts[0])
            seconds = Decimal(parts[1])
            total = Decimal(minutes) * Decimal('60') + seconds
            return total
        # segundos en decimal
        return Decimal(raw)
    except Exception:
        return Decimal('-1')

@require_GET
def tiempos_rally(request):
    """Tabla de mejores tiempos de Rally, de menor a mayor."""
    categoria = get_object_or_404(Categoria, nombre='rally')
    robots = Robot.objects.filter(categoria=categoria, activo=True)
    ranking = []
    for robot in robots:
        mejor = robot.mejor_tiempo()
        if mejor:
            ranking.append({
                'robot': robot,
                'nombre': robot.nombre,
                'autor_principal': robot.autor_principal,
                'autor_secundario': robot.autor_secundario,
                'mejor_tiempo': mejor,
            })
    ranking.sort(key=lambda x: x['mejor_tiempo'])
    rally_active = Tournament.objects.filter(categoria='rally', activo=True).order_by('-fecha_creacion').first()
    triadas_pendientes = False
    if rally_active:
        triadas_pendientes = rally_active.rally_triads.exists() and not rally_active.rounds.exists()
    return render(request, 'jurados/tiempos_rally.html', {
        'categoria': categoria,
        'ranking': ranking,
        'rally_active': rally_active,
        'triadas_pendientes': triadas_pendientes,
    })

@require_http_methods(["GET", "POST"])
def rally_llaves_top12(request):
    """Llaves al azar con Top 12 de Rally, con selección de ganadores (estado en sesión)."""
    categoria = get_object_or_404(Categoria, nombre='rally')

    def build_top12_list():
        robots = Robot.objects.filter(categoria=categoria, activo=True)
        ranking_local = []
        for r in robots:
            mt = r.mejor_tiempo()
            if mt:
                ranking_local.append({'id': r.id, 'nombre': r.nombre, 'tiempo': mt})
        ranking_local.sort(key=lambda x: x['tiempo'])
        return ranking_local[:12]

    def seed_initial_round(participants_list):
        import random
        shuffled = participants_list[:]
        random.shuffle(shuffled)
        matches_local = []
        for i in range(0, len(shuffled), 2):
            a = shuffled[i]
            b = shuffled[i+1] if i+1 < len(shuffled) else None
            matches_local.append({
                'a_id': a['id'], 'a_nombre': a['nombre'],
                'b_id': b['id'] if b else None, 'b_nombre': b['nombre'] if b else None,
                'winner_id': a['id'] if b is None else None,
                'is_bye': b is None,
            })
        return {'matches': matches_local}

    def winners_of_round(round_obj):
        wins = []
        for m in round_obj['matches']:
            if m['winner_id']:
                wins.append({'id': m['winner_id'], 'nombre': m['a_nombre'] if m['winner_id']==m['a_id'] else m['b_nombre']})
        return wins

    def all_set(round_obj):
        for m in round_obj['matches']:
            if not m['winner_id']:
                return False
        return True

    def make_next_round(prev_round):
        winners = winners_of_round(prev_round)
        if len(winners) <= 1:
            return None
        import random
        random.shuffle(winners)
        pairs = []
        for i in range(0, len(winners), 2):
            a = winners[i]
            b = winners[i+1] if i+1 < len(winners) else None
            pairs.append({
                'a_id': a['id'], 'a_nombre': a['nombre'],
                'b_id': b['id'] if b else None, 'b_nombre': b['nombre'] if b else None,
                'winner_id': a['id'] if b is None else None,
                'is_bye': b is None,
            })
        return {'matches': pairs}

    # Reset bracket if requested
    if request.method == 'POST' and request.POST.get('reset') == '1':
        if 'rally_top12_bracket' in request.session:
            del request.session['rally_top12_bracket']
        return redirect('jurados:rally_llaves_top12')

    # Initialize bracket in session if missing
    bracket = request.session.get('rally_top12_bracket')
    if not bracket:
        top12 = build_top12_list()
        initial = seed_initial_round(top12)
        bracket = {
            'rounds': [initial],
            'num_participants': len(top12),
        }
        request.session['rally_top12_bracket'] = bracket

    # Handle winner selection
    if request.method == 'POST' and request.POST.get('winner_id'):
        try:
            r_idx = int(request.POST.get('round_index'))
            m_idx = int(request.POST.get('match_index'))
            winner_id = int(request.POST.get('winner_id'))
        except (TypeError, ValueError):
            messages.error(request, 'Datos de partido inválidos.')
            return redirect('jurados:rally_llaves_top12')
        try:
            match_obj = bracket['rounds'][r_idx]['matches'][m_idx]
        except (IndexError, KeyError):
            messages.error(request, 'Partido no encontrado.')
            return redirect('jurados:rally_llaves_top12')
        # Validar ganador pertenezca al match
        if winner_id not in filter(None, [match_obj.get('a_id'), match_obj.get('b_id')]):
            messages.error(request, 'Ganador inválido para este partido.')
            return redirect('jurados:rally_llaves_top12')
        match_obj['winner_id'] = winner_id
        # Si ronda completa, generar siguiente
        if all_set(bracket['rounds'][r_idx]):
            nxt = make_next_round(bracket['rounds'][r_idx])
            if nxt:
                # truncar rondas futuras si existían
                bracket['rounds'] = bracket['rounds'][:r_idx+1]
                bracket['rounds'].append(nxt)
        request.session['rally_top12_bracket'] = bracket
        return redirect('jurados:rally_llaves_top12')

    return render(request, 'jurados/rally_llaves_top12.html', {
        'categoria': categoria,
        'rounds': bracket['rounds'],
        'num_participants': bracket['num_participants'],
    })

@require_http_methods(["POST"])
def rally_crear_torneo_top12(request):
    """Crea un Tournament persistente para Rally con el Top 12 y redirige a llaves (misma UX que Sumo)."""
    categoria = get_object_or_404(Categoria, nombre='rally')
    # Si ya hay un torneo activo de rally, no crear otro; redirigir al existente
    existente = Tournament.objects.filter(categoria='rally', activo=True).order_by('-fecha_creacion').first()
    if existente:
        # Si hay triadas pendientes, continúa ese flujo
        if existente.rally_triads.exists() and not existente.rounds.exists():
            messages.info(request, 'Ya existe una eliminatoria activa de Rally. Continuamos en llaves iniciales.')
            return redirect('jurados:rally_triadas', torneo_id=existente.id)
        # Si el existente está en otro formato (o ya tiene rondas), reinicia creando triadas
        existente.activo = False
        existente.save()
    robots = Robot.objects.filter(categoria=categoria, activo=True)
    ranking = []
    for r in robots:
        mt = r.mejor_tiempo()
        if mt:
            ranking.append({'id': r.id, 'nombre': r.nombre, 'tiempo': mt})
    ranking.sort(key=lambda x: x['tiempo'])
    top12 = ranking[:12]
    if not top12:
        messages.error(request, 'No hay suficientes tiempos para crear el torneo (se requieren al menos 2).')
        return redirect('jurados:tiempos_rally')
    # Desactivar torneos rally previos
    Tournament.objects.filter(categoria='rally', activo=True).update(activo=False)
    torneo = Tournament.objects.create(categoria='rally', nombre='Rally - Eliminatorias Top 12', activo=True)
    for p in top12:
        TournamentParticipant.objects.create(tournament=torneo, nombre=p['nombre'])
    # Crear triadas iniciales (3 por llave)
    create_rally_triads(torneo)
    messages.success(request, 'Torneo de Rally (Top 12) creado. Selecciona el ganador de cada triada para pasar a semifinales.')
    return redirect('jurados:rally_triadas', torneo_id=torneo.id)

@require_GET
def rally_triadas(request, torneo_id):
    torneo = get_object_or_404(Tournament, id=torneo_id, categoria='rally')
    triads = torneo.rally_triads.select_related('a','b','c','winner').order_by('index')
    if not triads.exists():
        # Si no hay triadas pero tampoco rondas, intenta sembrar desde cualquier ganador previo
        if torneo.rounds.exists():
            return redirect('jurados:torneo_detalle', torneo_id=torneo.id)
        # Si hay winners preexistentes (raro), generar semis
        seed_semifinals_from_triads(torneo)
        return redirect('jurados:torneo_detalle', torneo_id=torneo.id)
    # Si todas completas, crear semifinales (si aún no existen) y redirigir a llaves
    if rally_triads_completed(torneo):
        if not torneo.rounds.exists():
            seed_semifinals_from_triads(torneo)
        return redirect('jurados:torneo_detalle', torneo_id=torneo.id)
    return render(request, 'jurados/rally_triadas.html', {
        'torneo': torneo,
        'triads': triads,
    })

@require_http_methods(["POST"])
def rally_triada_winner(request, torneo_id, triad_id, winner_id):
    torneo = get_object_or_404(Tournament, id=torneo_id, categoria='rally')
    triad = get_object_or_404(torneo.rally_triads, id=triad_id)
    # Permitir que el ganador venga por POST (radio button) o por la URL
    try:
        post_winner = int(request.POST.get('winner_id')) if request.POST.get('winner_id') else None
    except (TypeError, ValueError):
        post_winner = None
    if post_winner:
        winner_id = post_winner
    if winner_id not in [getattr(triad.a, 'id', None), getattr(triad.b, 'id', None), getattr(triad.c, 'id', None)]:
        messages.error(request, 'Ganador inválido para esta triada.')
        return redirect('jurados:rally_triadas', torneo_id=torneo.id)
    triad.winner_id = winner_id
    triad.save()
    # Si todas completas, sembrar semifinales
    if rally_triads_completed(torneo):
        if not torneo.rounds.exists():
            seed_semifinals_from_triads(torneo)
        return redirect('jurados:torneo_detalle', torneo_id=torneo.id)
    return redirect('jurados:rally_triadas', torneo_id=torneo.id)

@require_GET
def dashboard(request):
    """Vista de dashboard TV con categorías: Fútbol, Sumo RC, Velocista"""
    # Obtener torneo activo de fútbol (si existe) y sus grupos y rondas
    torneo_futbol = Tournament.objects.filter(categoria='futbol', activo=True).first()
    futbol_data = None
    if torneo_futbol:
        grupos = torneo_futbol.football_groups.prefetch_related('teams__participant', 'matches__home__participant', 'matches__away__participant').all()
        rounds = torneo_futbol.rounds.prefetch_related('matches__a', 'matches__b', 'matches__winner').all()
        last_round_futbol = rounds.order_by('-index').first()
        futbol_data = {
            'torneo': torneo_futbol,
            'grupos': grupos,
            'rounds': rounds,
        }
    # Obtener torneos activos para sumo_rc y velocista si existen (en velocista mostramos ranking de robots)
    torneo_sumo = Tournament.objects.filter(categoria='sumo_rc', activo=True).first()
    rounds_sumo = torneo_sumo.rounds.prefetch_related('matches__a', 'matches__b', 'matches__winner').all() if torneo_sumo else []
    last_round_sumo = rounds_sumo.order_by('-index').first() if torneo_sumo else None

    # Para velocista usamos ranking desde modelos existentes
    categoria_velocista = Categoria.objects.filter(nombre='velocista').first()
    robots_vel = []
    if categoria_velocista:
        robots_queryset = categoria_velocista.robots.filter(activo=True)
        ranking = []
        for robot in robots_queryset:
            mt = robot.mejor_tiempo()
            if mt:
                ranking.append({'nombre': robot.nombre, 'mejor_tiempo': mt, 'autor_principal': robot.autor_principal})
        ranking.sort(key=lambda x: x['mejor_tiempo'])
        robots_vel = ranking

    context = {
        'futbol': futbol_data,
        'sumo_rounds': rounds_sumo,
        'futbol_last_round': last_round_futbol if torneo_futbol else None,
        'sumo_last_round': last_round_sumo,
        'velocista_ranking': robots_vel,
    }
    return render(request, 'jurados/dashboard.html', context)

@require_GET
def dashboard_rally(request, torneo_id: int = None):
    """Tablero TV para Rally: muestra llaves iniciales (triadas) y eliminatorias (semis/final)."""
    torneo = None
    if torneo_id:
        torneo = Tournament.objects.filter(id=torneo_id, categoria='rally', activo=True).first()
    if not torneo:
        torneo = Tournament.objects.filter(categoria='rally', activo=True).order_by('-fecha_creacion').first()
    triads = []
    rounds = []
    if torneo:
        triads = list(torneo.rally_triads.select_related('a','b','c','winner').order_by('index'))
        rounds = list(torneo.rounds.prefetch_related('matches__a','matches__b','matches__winner').all())
    return render(request, 'jurados/dashboard_rally.html', {
        'torneo': torneo,
        'triads': triads,
        'rounds': rounds,
    })

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
    
    # Verificar duplicados por nombre en la categoría (incluyendo inactivos)
    existente = Robot.objects.filter(categoria=categoria, nombre__iexact=nombre).first()
    if existente:
        if existente.activo:
            messages.error(request, f'Ya existe un robot con el nombre "{nombre}" en esta categoría.')
            return redirect('jurados:categoria_detalle', categoria_nombre=categoria_nombre)
        # Reactivar registro inactivo y actualizar datos
        existente.activo = True
        existente.autor_principal = autor_principal
        existente.autor_secundario = autor_secundario if autor_secundario else None
        existente.save()
        messages.success(request, f'Robot "{nombre}" reactivado exitosamente.')
        return redirect('jurados:categoria_detalle', categoria_nombre=categoria_nombre)

    # Crear nuevo con manejo de colisión de unicidad
    try:
        with transaction.atomic():
            Robot.objects.create(
                categoria=categoria,
                nombre=nombre,
                autor_principal=autor_principal,
                autor_secundario=autor_secundario if autor_secundario else None,
            )
        messages.success(request, f'Robot "{nombre}" agregado exitosamente.')
    except IntegrityError:
        # Ya existe uno creado simultáneamente; recuperar y notificar
        existente = Robot.objects.filter(categoria=categoria, nombre__iexact=nombre).first()
        if existente:
            if not existente.activo:
                existente.activo = True
                existente.autor_principal = autor_principal
                existente.autor_secundario = autor_secundario if autor_secundario else None
                existente.save()
                messages.success(request, f'Robot "{nombre}" reactivado exitosamente.')
            else:
                messages.info(request, f'El robot "{nombre}" ya existía en esta categoría.')
        else:
            messages.error(request, 'No se pudo crear el robot por una colisión de unicidad inesperada.')
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
    
    # Verificar que no existe otro robot con el mismo nombre en la categoría (incluye inactivos)
    if Robot.objects.filter(categoria=robot.categoria, nombre__iexact=nombre).exclude(id=robot.id).exists():
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
        tiempo = parse_time_input(request.POST.get('tiempo', '0'))
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
        nuevo_tiempo = parse_time_input(request.POST.get('tiempo', '0'))
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

def torneos_app(request):
    """Renderiza la app de torneos usando manifest de Vite para assets."""
    import json
    import os
    manifest_path = os.path.join(settings.BASE_DIR, 'jurados', 'static', 'torneos', '.vite', 'manifest.json')
    # Vite 5 default manifest in outDir root; also check fallback path
    if not os.path.exists(manifest_path):
        manifest_path = os.path.join(settings.BASE_DIR, 'jurados', 'static', 'torneos', 'manifest.json')
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        entry = manifest.get('index.html') or next(iter(manifest.values()))
        js_file = entry.get('file')
        css_files = entry.get('css', [])
        context = {
            'js_src': f"{settings.STATIC_URL}torneos/{js_file}" if js_file else None,
            'css_href': f"{settings.STATIC_URL}torneos/{css_files[0]}" if css_files else None,
        }
        return render(request, 'torneos.html', context)
    except Exception:
        # Fallback directo al index.html si existe
        index_path = os.path.join(settings.BASE_DIR, 'jurados', 'static', 'torneos', 'index.html')
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='text/html')
        return HttpResponse("No se encontró el build de torneos. Ejecuta npm run build en llave-maestra-torneos.", status=500)

# =====================
# Vistas Torneos Integrados
# =====================

@require_GET
def torneo_categoria(request, categoria: str):
    if categoria not in ['sumo_rc', 'sumo_autonomo', 'barcos', 'futbol']:
        messages.error(request, 'Categoría inválida.')
        return redirect('jurados:home')
    torneo = Tournament.objects.filter(categoria=categoria, activo=True).order_by('-fecha_creacion').first()
    if torneo:
        if categoria == 'futbol':
            return redirect('jurados:futbol_grupos', torneo_id=torneo.id)
        return redirect('jurados:torneo_detalle', torneo_id=torneo.id)
    # si no existe torneo activo, mostrar formulario de creación
    return redirect('jurados:torneo_nuevo', categoria=categoria)

@require_http_methods(["POST"]) 
def torneo_reiniciar(request, categoria: str):
    if categoria not in ['sumo_rc', 'sumo_autonomo', 'barcos', 'futbol', 'rally']:
        messages.error(request, 'Categoría inválida.')
        return redirect('jurados:home')
    pin = (request.POST.get('pin') or '').strip()
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('jurados:home')
    if pin != '0000':
        messages.error(request, 'PIN incorrecto. Operación cancelada.')
        return redirect(next_url)
    # desactivar torneos previos
    Tournament.objects.filter(categoria=categoria, activo=True).update(activo=False)
    messages.success(request, 'Torneo reiniciado. Crea uno nuevo para continuar.')
    # Para rally volvemos a Tiempos Rally, para otras categorías mantenemos flujo actual
    if categoria == 'rally':
        return redirect('jurados:tiempos_rally')
    return redirect('jurados:torneo_nuevo', categoria=categoria)

@require_http_methods(["GET", "POST"])
def torneo_nuevo(request, categoria):
    if categoria not in ['sumo_rc', 'sumo_autonomo', 'barcos', 'futbol']:
        return render(request, 'jurados/torneo_nuevo.html', {
            'error': 'Categoría inválida', 'categoria': categoria
        }, status=400)
    if request.method == 'GET':
        return render(request, 'jurados/torneo_nuevo.html', {
            'categoria': categoria
        })
    # POST
    nombre = request.POST.get('nombre', 'Torneo')
    participantes = [p.strip() for p in request.POST.get('participantes', '').split('\n') if p.strip()]
    if not participantes:
        messages.error(request, 'Debe ingresar al menos un participante (uno por línea).')
        return render(request, 'jurados/torneo_nuevo.html', {
            'categoria': categoria,
            'nombre': nombre,
            'participantes_text': request.POST.get('participantes', '')
        }, status=400)
    # desactivar torneos previos activos de esta categoría
    Tournament.objects.filter(categoria=categoria, activo=True).update(activo=False)
    torneo = Tournament.objects.create(categoria=categoria, nombre=nombre, activo=True)
    for p in participantes:
        TournamentParticipant.objects.create(tournament=torneo, nombre=p)
    if categoria == 'futbol':
        create_football_groups(torneo)
        messages.success(request, 'Torneo de Fútbol creado correctamente.')
        return redirect('jurados:futbol_grupos', torneo_id=torneo.id)
    else:
        create_initial_round(torneo)
        messages.success(request, 'Torneo creado correctamente.')
        return redirect('jurados:torneo_detalle', torneo_id=torneo.id)

@require_GET
def torneo_detalle(request, torneo_id):
    torneo = get_object_or_404(Tournament, id=torneo_id)
    rounds = list(torneo.rounds.prefetch_related('matches__a', 'matches__b', 'matches__winner'))
    context = {
        'torneo': torneo,
        'rounds': rounds,
        'participants': list(torneo.participants.all()),
    }
    return render(request, 'jurados/torneo_detalle.html', context)

@require_http_methods(["POST"])
def torneo_marcar_ganador(request, torneo_id, match_id, winner_participant_id):
    torneo = get_object_or_404(Tournament, id=torneo_id)
    match = get_object_or_404(TournamentMatch, id=match_id, round__tournament=torneo)
    winner = get_object_or_404(TournamentParticipant, id=winner_participant_id, tournament=torneo)
    match.winner = winner
    match.save()
    # Re-generar a partir de la ronda actual (permite edición retroactiva)
    regenerate_following_from(torneo, match.round)
    # Responder según tipo de petición
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, f'Se marcó ganador en el partido {match.id}.')
    return redirect('jurados:torneo_detalle', torneo_id=torneo.id)

@require_http_methods(["POST"])
def torneo_guardar_ganador(request, torneo_id, match_id):
    torneo = get_object_or_404(Tournament, id=torneo_id)
    match = get_object_or_404(TournamentMatch, id=match_id, round__tournament=torneo)
    try:
        winner_participant_id = int(request.POST.get('winner_participant_id'))
    except (TypeError, ValueError):
        messages.error(request, 'Debe seleccionar un ganador válido.')
        return redirect('jurados:torneo_detalle', torneo_id=torneo.id)
    winner = get_object_or_404(TournamentParticipant, id=winner_participant_id, tournament=torneo)
    match.winner = winner
    match.save()
    # Re-generar a partir de la ronda actual (permite edición retroactiva)
    regenerate_following_from(torneo, match.round)
    messages.success(request, 'Partido guardado.')
    return redirect('jurados:torneo_detalle', torneo_id=torneo.id)

@require_GET
def futbol_grupos(request, torneo_id):
    torneo = get_object_or_404(Tournament, id=torneo_id, categoria='futbol')
    grupos = torneo.football_groups.prefetch_related('teams__participant', 'matches__home__participant', 'matches__away__participant').all()
    context = {
        'torneo': torneo,
        'grupos': grupos,
        'has_rounds': torneo.rounds.exists(),
    }
    return render(request, 'jurados/futbol_grupos.html', context)

@require_GET
def torneo_ver_llaves(request, torneo_id):
    torneo = get_object_or_404(Tournament, id=torneo_id, categoria='futbol')
    # si no hay rondas y todos los partidos están jugados, generarlas
    if not torneo.rounds.exists() and are_all_group_matches_played(torneo):
        seed_knockout_from_groups(torneo)
        messages.success(request, 'Llaves generadas.')
    return redirect('jurados:torneo_detalle', torneo_id=torneo.id)

@require_http_methods(["POST"])
def futbol_registrar_resultado(request, torneo_id, match_id):
    torneo = get_object_or_404(Tournament, id=torneo_id, categoria='futbol')
    match = get_object_or_404(FootballGroupMatch, id=match_id, group__tournament=torneo)
    try:
        gh = int(request.POST.get('goals_home', '0'))
        ga = int(request.POST.get('goals_away', '0'))
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Goles inválidos'}, status=400)
    record_group_result(match, gh, ga)
    # Si todos los partidos de grupos están jugados, sembrar eliminación directa
    if are_all_group_matches_played(torneo):
        seed_knockout_from_groups(torneo)
        messages.success(request, 'Fase de grupos completada. Llaves generadas automáticamente.')
        return redirect('jurados:torneo_detalle', torneo_id=torneo.id)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, 'Resultado registrado correctamente.')
    return redirect('jurados:futbol_grupos', torneo_id=torneo.id)
