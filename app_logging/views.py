from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from .models import Log
from datetime import timedelta


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

@csrf_exempt
def update_log_date(request):
    if not (email := request.GET.get('email')):
        return JsonResponse({'error': 'Email is required'}, status=400)
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Buscar registros con estado success
    logs = Log.objects.filter(correo=email, tipo_evento='opcion3')

    if not logs.exists():
        return JsonResponse({'error': 'No logs found for this email'}, status=404)

    # Verificar si hay registros del día anterior
    if log_yesterday := logs.filter(fecha__date=yesterday).first():
        # Actualizar la fecha a hoy si hay un registro de ayer
        log_yesterday.fecha = timezone.now()
        log_yesterday.save()
        return JsonResponse({'message': 'Log date updated to today', 'log': log_yesterday.id})

    # Asignar fecha de ayer si no hay registro
    if log_today := logs.filter(fecha__date=today).first():
        return JsonResponse({'message': 'Log already exists for today', 'log': log_today.id})

    new_log = Log.objects.create(correo=email, tipo_evento='opcion3', observacion='Automatic update', nombre_aplicacion='IDS', tipo='Automatizacion')
    return JsonResponse({'message': 'Log created for yesterday', 'log': new_log.id})
