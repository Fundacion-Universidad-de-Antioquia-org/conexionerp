from django.db import models
from django.utils import timezone

class CtrlCapacitaciones(models.Model):
    
    fecha = models.DateField(default=timezone.now, verbose_name='Fecha de la sesión')
    hora_inicial = models.TimeField()
    hora_final = models.TimeField()
    moderador = models.CharField(max_length=60)
    area_encargada = models.CharField(max_length=200)
    ESTADO = [
        ('ACTIVA', 'ACTIVA'),
        ('CERRADA', 'CERRADA'),
    ]
    tema = models.CharField(max_length=60)
    estado = models.CharField(max_length=10, choices=ESTADO, default='ACTIVA')

    def __str__(self):
        return f"{self.tema} - {self.moderador}"