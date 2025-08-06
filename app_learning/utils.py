import logging
import json
import requests
import os
from django.utils.timezone import now

logger = logging.getLogger(__name__)

LOGGING_ENDPOINT = os.getenv('AZURE_LOGS')

def registrar_log_interno(username, observacion, tipo, id_registro):
    """
    Envía un log al servicio externo en Azure.
    """
    payload = {
        "correo": username,
        "fecha": now().isoformat(),
        "tipo_evento": "INFO",
        "observacion": observacion,
        "nombre_aplicacion": "Capacitaciones",
        "tipo": tipo,
        "id_registro": id_registro,
    }

    headers = {
        "Content-Type": "application/json",
        # "Authorization": f"Bearer {YOUR_TOKEN}",  # Si el endpoint exige autenticación
    }

    try:
        # Timeout corto para no bloquear la petición
        resp = requests.post(
            LOGGING_ENDPOINT,
            data=json.dumps(payload),
            headers=headers,
            timeout=2  # segundos
        )
        resp.raise_for_status()
        return resp.json()  # o resp.text, según lo que devuelva tu API
    except requests.exceptions.Timeout:
        logger.warning("Timeout al registrar log en Azure para %s", username)
    except requests.exceptions.RequestException as e:
        logger.error("Error enviando log a %s: %s", LOGGING_ENDPOINT, e)
    return None