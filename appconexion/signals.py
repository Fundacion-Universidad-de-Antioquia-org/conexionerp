# En algún archivo (por ejemplo, signals.py)

from django.db.models.signals import Signal
from django.dispatch import receiver
from datetime import datetime, time
from .utils import realizar_solicitud_http

mi_signal = Signal()

@receiver(mi_signal)
def ejecutar_solicitud_http(sender, **kwargs):
    ahora = datetime.now().time()
    hora_deseada = time(16, 25)  # 4:20 PM

    if ahora >= hora_deseada:
        realizar_solicitud_http()
