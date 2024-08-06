from django.db import models

class Log(models.Model):
    correo = models.EmailField()
    fecha = models.DateTimeField()
    tipo_evento = models.CharField(
        max_length=50,
        choices=[
            ('opcion1', 'INFO'),
            ('opcion2', 'ERROR'),
            ('opcion3', 'SUCCESS'),
       ],
    )
    observacion = models.CharField(max_length=255)
    nombre_aplicacion = models.CharField(max_length=50)
    tipo = models.CharField(
        max_length=50,
        choices=[
            ('opcion1', 'Automatizacion'),
            ('opcion2', 'Seguridad'),
            ('opcion3', 'Registro'),
       ],
    )
    def __str__(self):
        return f'{self.email} - {self.date} - {self.status}'
