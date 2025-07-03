from contextlib import nullcontext
from django.db import models
from django.utils import timezone

class CtrlCapacitaciones(models.Model):
    """
    Modelo para gestionar eventos de capacitación, reuniones y actividades de bienestar.
    Almacena información sobre fechas, horarios, participantes y detalles del evento.
    """
    
    # Campos de fecha y hora
    fecha = models.DateField(
        default=timezone.now, 
        verbose_name='Fecha de la sesión'
    )
    hora_inicial = models.TimeField(verbose_name='Hora de inicio')
    hora_final = models.TimeField(verbose_name='Hora de finalización')
    
    # Campos de responsables
    moderador = models.CharField(max_length=60, verbose_name='Moderador')
    responsable = models.CharField(max_length=60, default='', verbose_name='Responsable')
    area_encargada = models.CharField(max_length=100, verbose_name='Área encargada')
    
    # Opciones para campos de selección (Crear campo de verificacion de identidad)
    ESTADO = [
        ('ACTIVA', 'ACTIVA'),
        ('CERRADA', 'CERRADA'),
        ('CANCELADA', 'CANCELADA'),  # Nuevo estado agregado
        ('PENDIENTE', 'PENDIENTE'),
    ]
    
    MODALIDAD = [
        ('PRESENCIAL', 'PRESENCIAL'),
        ('VIRTUAL', 'VIRTUAL'),
        ('MIXTA', 'MIXTA'),
    ]

    VERIFICACION_IDENTIDAD = [
        ('SI', 'SI'),
        ('NO', 'NO'),
    ]
    
    TIPO = [
        ('Capacitación', 'Capacitación'),
        ('Reunión', 'Reunión'),
        ('Bienestar', 'Bienestar')
    ]
    
    PRIVACIDAD = [
        ('ABIERTA', 'ABIERTA'),
        ('CERRADA', 'CERRADA')
    ]
    
    # Campos de información del evento
    tema = models.CharField(max_length=60, verbose_name='Tema')
    objetivo = models.CharField(max_length=1200, verbose_name='Objetivo')
    temas = models.TextField(null=True, blank=True, verbose_name='Temas')
    
    # Campos de configuración
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO, 
        default='Capacitación', 
        verbose_name='Tipo de evento'
    )
    modalidad = models.CharField(
        max_length=10, 
        choices=MODALIDAD, 
        default='',
        verbose_name='Modalidad'
    )
    privacidad = models.CharField(
        max_length=20, 
        choices=PRIVACIDAD, 
        default='ABIERTA', 
        verbose_name='Privacidad'
    )
    estado = models.CharField(
        max_length=10, 
        choices=ESTADO, 
        default='ACTIVA',
        verbose_name='Estado'
    )
    verificacion_identidad = models.CharField(
        max_length=2,
        choices=VERIFICACION_IDENTIDAD,
        default='NO',
        null=True,
        blank=True,
        verbose_name='verificacion de identidad'
    )
    
    # Campos específicos según modalidad
    url_reunion = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name='URL de la Reunión'
    )
    ubicacion = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name='Ubicación'
    )
    
    # Campos de asistencia
    total_invitados = models.IntegerField(
        default=0, 
        verbose_name='Total Asistentes'
    )
    
    # Campos de recursos
    qr_base64 = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='Código QR (Base64)'
    )
    image_url = models.URLField(
        null=True, 
        blank=True,
        verbose_name='URL de imagen'
    )
    archivo_presentacion = models.URLField(
        null=True, 
        blank=True, 
        verbose_name='Archivo Presentación'
    )
    
    # Campos de sistema
    user = models.CharField(
        max_length=250, 
        default='user',
        verbose_name='Usuario creador'
    )
    
    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-fecha', 'hora_inicial']
    
    def __str__(self):
        return f"{self.tema} - {self.moderador}"
    
    def duracion_minutos(self):
        """Calcula la duración del evento en minutos"""
        if not self.hora_inicial or not self.hora_final:
            return 0
            
        inicio = self.hora_inicial
        fin = self.hora_final
        
        # Convertir a minutos para el cálculo
        inicio_minutos = inicio.hour * 60 + inicio.minute
        fin_minutos = fin.hour * 60 + fin.minute
        
        # Si fin es menor que inicio, asumimos que cruza la medianoche
        if fin_minutos < inicio_minutos:
            fin_minutos += 24 * 60
            
        return fin_minutos - inicio_minutos


class EventImage(models.Model):
    """
    Modelo para almacenar imágenes relacionadas con eventos de capacitación.
    """
    capacitacion = models.ForeignKey(
        CtrlCapacitaciones, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name='Evento'
    )
    image_url = models.URLField(
        max_length=500,
        verbose_name='URL de la imagen'
    )
    
    class Meta:
        verbose_name = 'Imagen de evento'
        verbose_name_plural = 'Imágenes de eventos'
    
    def __str__(self):
        return f"Imagen para {self.capacitacion.tema}"