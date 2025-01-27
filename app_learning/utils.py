import logging
from django.http import JsonResponse
from django.test import RequestFactory
import json
from dateutil import parser
from django.utils.timezone import make_aware, is_naive
from app_logging.views import registrar_log

logger = logging.getLogger(__name__)

def registrar_log_interno(correo, observacion, tipo):
    
    """
    Registra un log en la base de datos.
    :param correo: Correo del usuario relacionado con el log.
    :param tipo: Tipo del log (e.g., INFO, ERROR, WARN).
    :param observacion: Observación detallada del evento.
    :param nombre_aplicacion: Nombre de la aplicación donde ocurre el evento.
    :param fecha: Fecha del evento (ISO 8601). Si no se proporciona, se usa la fecha actual.
    :param tipo_evento: Tipo de evento relacionado con el log.
    :return: Diccionario con el resultado del registro.
    """
    try:
        factory = RequestFactory()
        # Si no se proporciona fecha, usar la fecha actual
        if fecha is None:
            fecha = make_aware(parser.parse(fecha)) if is_naive(parser.parse(fecha)) else parser.parse(fecha)
 
        # Crear el registro de log
        log = {
            "correo": correo,
            "fecha": fecha,
            "tipo_evento": "INFO",
            "observacion": observacion,
            "nombre_aplicacion": "Capacitaciones",
            "tipo": tipo,
        }

        # Crear una solicitud POST simulada
        request = factory.post(
        "/app_logging/registrar_log/",
        data=json.dumps(log),
        content_type="application/json" 
    )
        # Llamar directamente a la función
        response = registrar_log(request)
        return response
    except Exception as e:
        logger.error(f"Error al registrar el log: {e}")
 
   