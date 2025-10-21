from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class Categoria(models.Model):
    """Modelo para las categorías de competencia"""
    CATEGORIAS_CHOICES = [
        ('rally', 'Rally'),
        ('futbol', 'Fútbol'),
        ('sumo_rc', 'Sumo RC'),
        ('sumo_autonomo', 'Sumo Autónomo'),
        ('barcos', 'Barcos'),
        ('velocista', 'Velocista'),
    ]
    
    nombre = models.CharField(max_length=20, choices=CATEGORIAS_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']
    
    def __str__(self):
        return self.get_nombre_display()

class Robot(models.Model):
    """Modelo para los robots participantes"""
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='robots')
    nombre = models.CharField(max_length=100)
    autor_principal = models.CharField(max_length=100)
    autor_secundario = models.CharField(max_length=100, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Robot"
        verbose_name_plural = "Robots"
        ordering = ['nombre']
        unique_together = ['categoria', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.categoria}"
    
    def mejor_tiempo(self):
        """Retorna el mejor tiempo del robot"""
        mejor = self.tiempos.filter(valido=True).order_by('tiempo').first()
        return mejor.tiempo if mejor else None

class SesionRegistro(models.Model):
    """Modelo para controlar las sesiones de registro de tiempo"""
    robot = models.ForeignKey(Robot, on_delete=models.CASCADE, related_name='sesiones')
    activa = models.BooleanField(default=False)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    usuario = models.CharField(max_length=100, default='Jurado')
    
    class Meta:
        verbose_name = "Sesión de Registro"
        verbose_name_plural = "Sesiones de Registro"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        estado = "Activa" if self.activa else "Finalizada"
        return f"Sesión {self.robot.nombre} - {estado}"
    
    def finalizar(self):
        """Finaliza la sesión de registro"""
        self.activa = False
        self.fecha_fin = timezone.now()
        self.save()

class TiempoRegistro(models.Model):
    """Modelo para los tiempos registrados"""
    robot = models.ForeignKey(Robot, on_delete=models.CASCADE, related_name='tiempos')
    tiempo = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0.0)])
    fecha_registro = models.DateTimeField(auto_now_add=True)
    metodo_registro = models.CharField(max_length=20, choices=[
        ('esp32', 'ESP32'),
        ('manual', 'Manual'),
    ], default='esp32')
    valido = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    sesion = models.ForeignKey(SesionRegistro, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Tiempo Registrado"
        verbose_name_plural = "Tiempos Registrados"
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.robot.nombre} - {self.tiempo}s"

# =====================
# Modelos de Torneos
# =====================

class Tournament(models.Model):
    """Torneo para categorías por eliminación u otras (excepto Rally/Velocista)."""
    CATEGORIAS_TORNEO = [
        ('sumo_rc', 'Sumo RC'),
        ('sumo_autonomo', 'Sumo Autónomo'),
        ('barcos', 'Barcos RC'),
        ('futbol', 'Fútbol RC'),
        ('rally', 'Rally'),
    ]

    categoria = models.CharField(max_length=20, choices=CATEGORIAS_TORNEO)
    nombre = models.CharField(max_length=100, default='Torneo')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"

class TournamentParticipant(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='participants')
    nombre = models.CharField(max_length=100)

    class Meta:
        unique_together = ('tournament', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class TournamentRound(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='rounds')
    index = models.PositiveIntegerField(default=0)
    nombre = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['index']

    def __str__(self):
        return f"{self.nombre} (#{self.index + 1})"

class TournamentMatch(models.Model):
    round = models.ForeignKey(TournamentRound, on_delete=models.CASCADE, related_name='matches')
    a = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True, blank=True, related_name='match_as_a')
    b = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True, blank=True, related_name='match_as_b')
    winner = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True, blank=True, related_name='match_wins')
    is_bye = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        a = self.a.nombre if self.a else 'TBD'
        b = self.b.nombre if self.b else 'TBD'
        return f"{a} vs {b}"

# Triadas iniciales específicas de Rally (3 robots por llave, pasa 1)
class RallyTriad(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='rally_triads')
    index = models.PositiveIntegerField(default=0)  # 0..3 para Top12
    a = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True, blank=True, related_name='rally_triad_a')
    b = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True, blank=True, related_name='rally_triad_b')
    c = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True, blank=True, related_name='rally_triad_c')
    winner = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True, blank=True, related_name='rally_triad_winner')

    class Meta:
        ordering = ['index']

    def __str__(self):
        names = [p.nombre for p in [self.a, self.b, self.c] if p]
        return f"Triada {self.index + 1}: {', '.join(names)}"

# Fase de grupos para Fútbol RC
class FootballGroup(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='football_groups')
    codigo = models.CharField(max_length=2)  # A, B, C...
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('tournament', 'codigo')
        ordering = ['codigo']

    def __str__(self):
        return f"Grupo {self.codigo}"

class FootballTeam(models.Model):
    group = models.ForeignKey(FootballGroup, on_delete=models.CASCADE, related_name='teams')
    participant = models.ForeignKey(TournamentParticipant, on_delete=models.CASCADE)
    pj = models.IntegerField(default=0)
    g = models.IntegerField(default=0)
    e = models.IntegerField(default=0)
    p = models.IntegerField(default=0)
    gf = models.IntegerField(default=0)
    gc = models.IntegerField(default=0)
    dg = models.IntegerField(default=0)
    pts = models.IntegerField(default=0)

    class Meta:
        unique_together = ('group', 'participant')
        ordering = ['-pts', '-dg', '-gf', 'participant__nombre']

    def __str__(self):
        return f"{self.participant.nombre} ({self.group})"

class FootballGroupMatch(models.Model):
    group = models.ForeignKey(FootballGroup, on_delete=models.CASCADE, related_name='matches')
    home = models.ForeignKey(FootballTeam, on_delete=models.CASCADE, related_name='home_matches')
    away = models.ForeignKey(FootballTeam, on_delete=models.CASCADE, related_name='away_matches')
    goals_home = models.IntegerField(null=True, blank=True)
    goals_away = models.IntegerField(null=True, blank=True)
    played = models.BooleanField(default=False)

    class Meta:
        unique_together = ('group', 'home', 'away')
        ordering = ['id']

    def __str__(self):
        return f"{self.home.participant.nombre} vs {self.away.participant.nombre}"