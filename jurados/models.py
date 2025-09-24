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
