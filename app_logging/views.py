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
"""
def update_log_date(request):
    logger.debug("Request received for update_log_date")

    if not (correo := request.GET.get('correo')):
        logger.error("Correo is required")
        return JsonResponse({'error': 'Correo is required'}, status=400)

    logger.debug(f"Correo received: {correo}")

    now = timezone.now()
    today = now.date()

    logger.debug(f"Searching for logs with correo: {correo}")

    # Obtener el último log registrado por el usuario (sin importar la fecha)
    last_log = Log.objects.filter(correo=correo, tipo_evento='SUCCESS').order_by('-fecha').first()

    if not last_log:
        # No hay logs registrados, asignamos la fecha de hoy
        logger.debug("No logs found for the given correo, assigning today's date.")
        return JsonResponse({'message': 'First log entry, using today\'s date', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})

    last_reported_date = last_log.fecha.date()  # Extraer solo la fecha del último log registrado
    logger.debug(f"Last reported date: {last_reported_date}")

    # Determinar la próxima fecha pendiente
    expected_next_date = last_reported_date + timedelta(days=1)
    logger.debug(f"Expected next reporting date: {expected_next_date}")

    if expected_next_date >= today:
        # Si la próxima fecha a reportar es hoy o futura, usar esa fecha
        logger.debug(f"Next reporting date is today or future ({expected_next_date}), assigning today's date.")
        return JsonResponse({'message': 'Log already exists for today', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})
    else:
        # Si hay días pendientes de reporte, asignar la primera fecha sin registrar
        requires_justification = now.hour >= 12  # Si es después del mediodía, se requiere justificación
        logger.debug(f"Pending date to be reported: {expected_next_date}, requires justification: {requires_justification}")

        return JsonResponse({'message': 'Pending log date', 'new_date': expected_next_date.strftime('%Y-%m-%d'), 'requires_justification': requires_justification})
"""


def update_log_date(request):
    logger.debug("Request received for update_log_date")

    if not (correo := request.GET.get('correo')):
        logger.error("Correo is required")
        return JsonResponse({'error': 'Correo is required'}, status=400)

    logger.debug(f"Correo received: {correo}")

    now = timezone.now()  # Fecha y hora actual con zona horaria
    today = now.date()

    logger.debug(f"Searching for logs with correo: {correo}")

    # Obtener el último log registrado por el usuario
    last_log = Log.objects.filter(correo=correo, tipo_evento='SUCCESS').order_by('-fecha').first()

    if not last_log:
        logger.debug("No logs found for the given correo, assigning today's date.")
        return JsonResponse({
            'message': 'First log entry, using today\'s date',
            'new_date': today.strftime('%Y-%m-%d'),
            'requires_justification': False
        })

    last_reported_date = last_log.fecha.date()
    logger.debug(f"Last reported date: {last_reported_date}")

    # Determinar la próxima fecha pendiente
    expected_next_date = last_reported_date + timedelta(days=1)
    logger.debug(f"Expected next reporting date: {expected_next_date}")

    # Calcular el mediodía del día siguiente después del último reporte
    justification_deadline = last_reported_date + timedelta(days=2)  # Día siguiente + 12 horas
    justification_deadline = timezone.make_aware(
        timezone.datetime.combine(justification_deadline, timezone.datetime.min.time()) + timedelta(hours=12),
        timezone.get_current_timezone()
    )

    # Asegurar que `now` sea `aware`
    if timezone.is_naive(now):
        now = timezone.make_aware(now, timezone.get_current_timezone())

    # Determinar si se requiere justificación
    requires_justification = now >= justification_deadline
    logger.debug(f"Justification deadline: {justification_deadline}, Requires justification: {requires_justification}")

    if expected_next_date >= today:
        logger.debug(f"Next reporting date is today or future ({expected_next_date}), assigning today's date.")
        return JsonResponse({
            'message': 'Log already exists for today',
            'new_date': today.strftime('%Y-%m-%d'),
            'requires_justification': requires_justification
        })
    else:
        logger.debug(f"Pending date to be reported: {expected_next_date}, requires justification: {requires_justification}")
        return JsonResponse({
            'message': 'Pending log date',
            'new_date': expected_next_date.strftime('%Y-%m-%d'),
            'requires_justification': requires_justification
        })
    