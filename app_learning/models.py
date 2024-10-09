from django.db import models
from django.utils import timezone

class CtrlCapacitaciones(models.Model):
    
    fecha = models.DateField(default=timezone.now, verbose_name='Fecha de la sesión')
    hora_inicial = models.TimeField()
    hora_final = models.TimeField()
    moderador = models.CharField(max_length=60)
    area_encargada = models.CharField(max_length=100)
    ESTADO = [
        ('ACTIVA', 'ACTIVA'),
        ('CERRADA', 'CERRADA'),
    ]
    MODALIDAD = [
        ('PRESENCIAL', 'PRESENCIAL'),
        ('VIRTUAL', 'VIRTUAL'),
        ('MIXTA', 'MIXTA'),
    ]
    tema = models.CharField(max_length=60)
    modalidad = models.CharField(max_length=10, choices=MODALIDAD, default='')
    url_reunion = models.CharField(max_length=255, blank=True, null=True, verbose_name='URL de la Reunión')
    ubicacion = models.CharField(max_length=255, blank=True, null=True, verbose_name='Ubicación')
    estado = models.CharField(max_length=10, choices=ESTADO, default='ACTIVA')
    objetivo = models.CharField(max_length=255)
    responsable = models.CharField(max_length=60, default='')
    qr_base64 = models.TextField(blank=True, null=True)  # Campo para almacenar el QR en base64
    total_invitados = models.IntegerField(default=0, verbose_name='Total Asistentes')

    def __str__(self):
        return f"{self.tema} - {self.moderador}"