from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.http import JsonResponse
from .models import Log
from datetime import timedelta
import logging
from dateutil import parser
from django.utils.timezone import make_aware, is_naive
import pytz


"""@csrf_exempt
def registrar_log(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        correo = data.get('correo')
        fecha = data.get('fecha')
        tipo_evento = data.get('tipo_evento')
        observacion = data.get('observacion') 
        nombre_aplicacion = data.get('nombre_aplicacion') 
        tipo = data.get('tipo') 

        log = Log.objects.create(correo=correo, fecha=fecha, tipo_evento=tipo_evento,observacion=observacion, nombre_aplicacion=nombre_aplicacion,tipo=tipo)
        return JsonResponse({'message': 'Log registrado correctamente'}, status=201)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

logger = logging.getLogger(__name__)"""



logger = logging.getLogger(__name__)
@csrf_exempt
def registrar_log(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    data = json.loads(request.body)
    correo = data.get('correo')
    fecha_str = data.get('fecha')
    tipo_evento = data.get('tipo_evento')
    observacion = data.get('observacion')
    nombre_aplicacion = data.get('nombre_aplicacion')
    tipo = data.get('tipo')
    id_registro = data.get('id_registro')

    try:
        fecha = parser.isoparse(fecha_str)
        #
        # Convertir la fecha a la zona horaria de Colombia
        
        #colombia_tz = pytz.timezone('America/Bogota')
        #if is_naive(fecha):
        #    fecha = make_aware(fecha, timezone=colombia_tz)
        #else:
        #    fecha = fecha.astimezone(colombia_tz)
    except Exception as e:
        logger.error(f"Error al parsear la fecha: {e}")
        return JsonResponse({'error': 'Fecha inválida'}, status=400)

    log = Log.objects.create(correo=correo, fecha=fecha, tipo_evento=tipo_evento, observacion=observacion, nombre_aplicacion=nombre_aplicacion, tipo=tipo, id_registro=id_registro)
    return JsonResponse({'message': 'Log registrado correctamente'}, status=201)

def update_log_date(request):
    logger.debug("Request received for update_log_date")

    if not (correo := request.GET.get('correo')):
        logger.error("Correo is required")
        return JsonResponse({'error': 'Correo is required'}, status=400)

    logger.debug(f"Correo received: {correo}")

    now = timezone.now()
    today = now.date()
    yesterday = today - timedelta(days=1)

    logger.debug(f"Searching for logs with correo: {correo}")
    logs = Log.objects.filter(correo=correo, tipo_evento='SUCCESS')
    logger.debug(f"Logs found: {logs.count()}")

    if not logs.exists():
        # No hay logs con ese correo, es el primer registro, asignar la fecha actual
        logger.debug("No logs found for the given correo, assigning today's date.")
        return JsonResponse({'message': 'First log entry, using today\'s date', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})

    log_yesterday = logs.filter(fecha__date=yesterday).first()
    log_today = logs.filter(fecha__date=today).first()

    if log_yesterday:
        logger.debug(f"Log found for yesterday with log id: {log_yesterday.id}")
        if log_today:
            # Si ya hay un registro para hoy, usamos la fecha de hoy y no se requiere justificación
            logger.debug(f"Log already exists for today with log id: {log_today.id}")
            return JsonResponse({'message': 'Log already exists for today', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})
        else:
            # No hay registro para hoy, pero hay registro para ayer
            logger.debug("No log found for today, but log found for yesterday. Using today's date.")
            return JsonResponse({'message': 'Log date is today', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})
    else:
        # No hay registro para ayer
        logger.debug("No log found for yesterday. Using yesterday's date.")
        if now.hour < 12:
            # Antes de las 12:00 pm, usamos la fecha de ayer y no se requiere justificación
            return JsonResponse({'message': 'Log date is yesterday, no justification required', 'new_date': yesterday.strftime('%Y-%m-%d'), 'requires_justification': False})
        else:
            # Después de las 12:00 pm, usamos la fecha de ayer y se requiere justificación
            return JsonResponse({'message': 'Log date is yesterday, justification required', 'new_date': yesterday.strftime('%Y-%m-%d'), 'requires_justification': True})

    # En caso de cualquier otro escenario, usamos la fecha de hoy y no se requiere justificación
    logger.debug("Using today's date without requiring justification.")
    return JsonResponse({'message': 'Log date is today, no justification required', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})

    
"""def update_log_date(request):
    logger.debug("Request received for update_log_date")

    if not (correo := request.GET.get('correo')):
        logger.error("Correo is required")
        return JsonResponse({'error': 'Correo is required'}, status=400)

    logger.debug(f"Correo received: {correo}")

    now = timezone.now()
    today = now.date()
    yesterday = today - timedelta(days=1)

    logger.debug(f"Searching for logs with correo: {correo}")
    logs = Log.objects.filter(correo=correo, tipo_evento='SUCCESS')
    logger.debug(f"Logs found: {logs.count()}")

    if not logs.exists():
        logger.error(f"No logs found for correo: {correo}")
        return JsonResponse({'error': 'No logs found for this correo'}, status=404)

    log_yesterday = logs.filter(fecha__date=yesterday).first()
    log_today = logs.filter(fecha__date=today).first()

    if log_yesterday:
        logger.debug(f"Log found for yesterday with log id: {log_yesterday.id}")
        if log_today:
            # Si ya hay un registro para hoy, usamos la fecha de hoy y no se requiere justificación
            logger.debug(f"Log already exists for today with log id: {log_today.id}")
            return JsonResponse({'message': 'Log already exists for today', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})
        else:
            # No hay registro para hoy, pero hay registro para ayer
            logger.debug("No log found for today, but log found for yesterday. Using today's date.")
            return JsonResponse({'message': 'Log date is today', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})
    else:
        # No hay registro para ayer
        logger.debug("No log found for yesterday. Using yesterday's date.")
        if now.hour < 12:
            # Antes de las 12:00 pm, usamos la fecha de ayer y no se requiere justificación
            return JsonResponse({'message': 'Log date is yesterday, no justification required', 'new_date': yesterday.strftime('%Y-%m-%d'), 'requires_justification': False})
        else:
            # Después de las 12:00 pm, usamos la fecha de ayer y se requiere justificación
            return JsonResponse({'message': 'Log date is yesterday, justification required', 'new_date': yesterday.strftime('%Y-%m-%d'), 'requires_justification': True})

    # En caso de cualquier otro escenario, usamos la fecha de hoy y no se requiere justificación
    logger.debug("Using today's date without requiring justification.")
    return JsonResponse({'message': 'Log date is today, no justification required', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})"""