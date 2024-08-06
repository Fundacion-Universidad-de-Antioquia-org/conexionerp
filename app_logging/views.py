from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.http import JsonResponse
from .models import Log
from datetime import timedelta
import logging


@csrf_exempt
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

logger = logging.getLogger(__name__)
"""
def update_log_date(request):
    logger.debug("Request received for update_log_date")
    
    if not (correo := request.GET.get('correo')):
        logger.error("Correo is required")
        return JsonResponse({'error': 'Correo is required'}, status=400)
    
    logger.debug(f"Correo received: {correo}")
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    logger.debug(f"Searching for logs with correo: {correo}")
    logs = Log.objects.filter(correo=correo, tipo_evento='SUCCESS')
    logger.debug(f"Logs found: {logs.count()}")

    if not logs.exists():
        logger.error(f"No logs found for correo: {correo}")
        return JsonResponse({'error': 'No logs found for this correo'}, status=404)

    if log_yesterday := logs.filter(fecha__date=yesterday).first():
        log_yesterday.fecha = timezone.now()
        log_yesterday.save()
        logger.debug(f"Log found for yesterday. Updating date to today for log id: {log_yesterday.id}")
        return JsonResponse({'message': 'Log date updated to today', 'new_date': today.strftime('%Y-%m-%d')})

    if log_today := logs.filter(fecha__date=today).first():
        logger.debug(f"Log already exists for today with log id: {log_today.id}")
        return JsonResponse({'message': 'Log already exists for today', 'new_date': today.strftime('%Y-%m-%d')})

    logger.debug("No log found for today or yesterday. Setting date to yesterday.")
    return JsonResponse({'message': 'No log found for today or yesterday, setting date to yesterday', 'new_date': yesterday.strftime('%Y-%m-%d')})"""
    
    

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
        logger.error(f"No logs found for correo: {correo}")
        return JsonResponse({'error': 'No logs found for this correo'}, status=404)

    log_yesterday = logs.filter(fecha__date=yesterday).first()
    if log_today := logs.filter(fecha__date=today).first():
        # Si ya hay un registro para hoy, usamos la fecha de hoy
        logger.debug(f"Log already exists for today with log id: {log_today.id}")
        return JsonResponse({'message': 'Log already exists for today', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})
    elif log_yesterday:
        # Si hay un registro para ayer, verificamos la hora actual
        if now.hour < 12:
            # Antes de las 12:00 pm, usamos la fecha de ayer
            logger.debug(f"Log found for yesterday. Using yesterday's date for log id: {log_yesterday.id}")
            return JsonResponse({'message': 'Log date is yesterday', 'new_date': yesterday.strftime('%Y-%m-%d'), 'requires_justification': False})
        else:
            # Después de las 12:00 pm, usamos la fecha de hoy pero requerimos justificación
            logger.debug(
                "Log found for yesterday but it is after 12:00 pm. Using today's date and requiring justification."
            )
            return JsonResponse({'message': 'Log date is today, justification required', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': True})

    # No hay registros para hoy ni para ayer, usamos la fecha de hoy sin justificación
    logger.debug("No log found for today or yesterday. Using today's date without requiring justification.")
    return JsonResponse({'message': 'Log date is today, no justification required', 'new_date': today.strftime('%Y-%m-%d'), 'requires_justification': False})