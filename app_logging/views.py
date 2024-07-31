from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Log
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
import datetime
import json


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
def consultar_logs(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        correo = data.get('correo')
        fecha = parse_date(data.get('fecha'))
        if correo and fecha:
            # Obtener la fecha del día anterior
            fecha_anterior = fecha - datetime.timedelta(days=1)
            # Verificar si existe un registro con la fecha del día anterior y estado 'SUCCESS'
            registro_existe = Log.objects.filter(correo=correo, fecha__date=fecha_anterior, tipo_evento='SUCCESS').exists()
            
            if registro_existe:
                return JsonResponse({'status': 'existe_registro', 'fecha_actual': str(fecha)})
            else:
                return JsonResponse({'status': 'no_existe_registro', 'fecha_anterior': str(fecha_anterior)})
        return JsonResponse({'status': 'error', 'message': 'Correo o fecha no proporcionados'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)