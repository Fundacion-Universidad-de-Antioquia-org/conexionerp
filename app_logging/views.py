from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import get_object_or_404
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

def update_log_date(request):
    logger.debug("Request received for update_log_date")
    
    email = request.GET.get('email')
    if not email:
        logger.error("Email is required")
        return JsonResponse({'error': 'Email is required'}, status=400)
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    logger.debug(f"Searching for logs with email: {email}")
    logs = Log.objects.filter(correo=email, tipo_evento='opcion3')

    if not logs.exists():
        logger.error(f"No logs found for email: {email}")
        return JsonResponse({'error': 'No logs found for this email'}, status=404)

    if log_yesterday := logs.filter(fecha__date=yesterday).first():
        log_yesterday.fecha = timezone.now()
        log_yesterday.save()
        logger.debug(f"Log found for yesterday. Updating date to today for log id: {log_yesterday.id}")
        return JsonResponse({'message': 'Log date updated to today', 'new_date': today.strftime('%Y-%m-%d')})

    if log_today := logs.filter(fecha__date=today).first():
        logger.debug(f"Log already exists for today with log id: {log_today.id}")
        return JsonResponse({'message': 'Log already exists for today', 'new_date': today.strftime('%Y-%m-%d')})

    logger.debug("No log found for today or yesterday. Setting date to yesterday.")
    return JsonResponse({'message': 'No log found for today or yesterday, setting date to yesterday', 'new_date': yesterday.strftime('%Y-%m-%d')})
