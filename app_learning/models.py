from django.db import models
from django.utils import timezone

class CtrlCapacitaciones(models.Model):
    fecha = models.DateField(default=timezone.now, verbose_name='Fecha de la sesión')
    hora_inicial = models.TimeField()
    hora_final = models.TimeField()
    moderador = models.CharField(max_length=60)
    AREA_OPCIONES = [
        ('opcion1', 'Opción 1'),
        ('opcion2', 'Opción 2'),
    ]
    ESTADO = [
        ('ACTIVA', 'ACTIVA'),
        ('CERRADA', 'CERRADA'),
    ]
    area_encargada = models.CharField(max_length=20, choices=AREA_OPCIONES,)
    tema = models.CharField(max_length=60)
    estado = models.CharField(max_length=10, choices=ESTADO, default='ACTIVA')

    def __str__(self):
        return f"{self.tema} - {self.moderador}"