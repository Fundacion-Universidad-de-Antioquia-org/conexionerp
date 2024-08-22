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
    tema = models.CharField(max_length=60)
    estado = models.CharField(max_length=10, choices=ESTADO, default='ACTIVA')
    objetivo = models.CharField(max_length=161)
    qr_base64 = models.TextField(blank=True, null=True)  # Campo para almacenar el QR en base64

    def __str__(self):
        return f"{self.tema} - {self.moderador}"