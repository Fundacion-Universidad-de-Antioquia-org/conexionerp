import qrcode
import pytz
import logging
import base64
import openpyxl
import xmlrpc.client
import unicodedata
import os
import traceback
from django.contrib import messages
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CtrlCapacitacionesForm, RegistrationForm
from .models import CtrlCapacitaciones, EventImage
from django.http import HttpResponseRedirect
from django.urls import reverse
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote, unquote, urlparse
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import registrar_log_interno
 

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
database = os.getenv("DATABASE")
user = os.getenv("ODOO_USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
apphost = os.getenv('APP_HOST')

@settings.AUTH.login_required
def index(request, *, context):
    user = context['user']
    return HttpResponse(f"Hello, {user.get('name')}.")

def get_employee_names(request):
    ids = request.GET.getlist('ids[]', [])
    if ids:
        try:
            common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
            uid = common.authenticate(database, user, password, {})
            models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

            # Buscar empleados por identificación
            employees = models.execute_kw(database, uid, password,
                                          'hr.employee', 'search_read',
                                          [[['identification_id', 'in', ids]]],
                                          {'fields': ['id', 'name', 'identification_id']})

            results = [{'id': emp['identification_id'], 'name': emp['name']} for emp in employees]
            return JsonResponse({'results': results})
        except Exception as e:
            logger.error('Failed to fetch employee names from Odoo', exc_info=True)
            return JsonResponse({'error': 'Error fetching employee names'}, status=500)
    else:
        return JsonResponse({'results': []})


def upload_to_azure_blob(file, filename):
    print('Intentando subir archivo a Azure Blob Storage...')
    try:
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_CONTAINER_NAME")

        if not connection_string or not container_name:
            print("Error: La cadena de conexión o el nombre del contenedor no están configurados.")
            return None

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)

        # Subir el archivo
        blob_client.upload_blob(file, overwrite=True)
        print(f"Archivo subido a: {blob_client.url}")

        return blob_client.url
    except Exception as e:
        print(f"Error subiendo el archivo a Azure Blob Storage: {e}")
        import traceback
        traceback.print_exc()
        return None

def delete_blob_from_azure(blob_url):
    try:
        # Obtener la cadena de conexión desde las variables de entorno
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Extraer el nombre del contenedor y del blob desde la URL
        parsed_url = urlparse(blob_url)
        path_parts = parsed_url.path.lstrip('/').split('/', 1)
        container_name = path_parts[0]
        blob_name = unquote(path_parts[1])

        print('Nombre del contenedor:', container_name)
        print('Nombre del blob:', blob_name)
        
        # Obtener el cliente del blob
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        # Eliminar el blob
        blob_client.delete_blob()
        
        print("Blob eliminado exitosamente.")
        return True
    except Exception as e:
        print(f"Error eliminando el blob de Azure Blob Storage: {e}")
        traceback.print_exc()
        return False

# Vista para eliminar imagenes
def delete_image(request, image_id):
    image = get_object_or_404(EventImage, id=image_id)
    capacitacion_id = image.capacitacion.id

    if request.method == 'POST':
        # Eliminar el blob de Azure Blob Storage
        success = delete_blob_from_azure(image.image_url)
        if success:
            # Eliminar la instancia de la imagen
            image.delete()
            messages.success(request, "La imagen ha sido eliminada exitosamente.")
        else:
            messages.error(request, "Hubo un error al eliminar la imagen.")
    else:
        messages.error(request, "Solicitud inválida.")

    return redirect('view_assistants', id=capacitacion_id)


# Conversión a UTC asegurando que el objeto sea datetime
def convert_to_utc(dt, timezone_str):
    if isinstance(dt, datetime):
        local = pytz.timezone(timezone_str)
        local_dt = local.localize(dt, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt
    else:
        raise ValueError("El objeto proporcionado no es de tipo datetime.datetime")

# Función para obtener el ID del departamento
def get_department_id(department_name):
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        department = models.execute_kw(database, uid, password,
            'hr.department', 'search_read',
            [[['name', '=', department_name]]],
            {'fields': ['id'], 'limit': 1})
        
        if department:
            return department[0]['id']
        else:
            return None
    
    except Exception as e:
        logger.error('Failed to fetch department ID from Odoo', exc_info=True)
        return None

# Función para obtener el ID del empleado por Nombre
def get_employee_id_by_name(name):
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        employees = models.execute_kw(database, uid, password,
            'hr.employee', 'search_read',
            [[['name', '=', name]]],
            {'fields': ['id'], 'limit': 1})
        
        if employees:
            return employees[0]['id']
        else:
            return None
        
    except Exception as e:
        logger.error('Failed to fetch employee ID from Odoo', exc_info=True)
        return None


# Función para enviar datos a Odoo
def send_to_odoo(data):
    logger.debug(f"Intentando enviar datos a Odoo: {data}")
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        department_id = get_department_id(data['department'])
        if not department_id:
            raise ValueError(f"Department '{data['department']}' not found in Odoo")

        # Verificar si 'employee_id' está en 'data'; si no, buscarlo
        if 'employee_id' in data and data['employee_id']:
            employee_id = data['employee_id']
        else:
            # Buscar el empleado por 'document_id' si 'employee_id' no está disponible
            employee_data = models.execute_kw(database, uid, password,
                                              'hr.employee', 'search_read',
                                              [[['name', '=', data['document_id']]]],
                                              {'fields': ['id', 'name'], 'limit': 1})
            print('DATOS: ', employee_data)

            if not employee_data:
                raise ValueError(f"Empleado con documento '{data['document_id']}' no encontrado en Odoo")

            employee_id = employee_data[0]['id']

       # Convertir fechas a cadenas en UTC
        date_str = data['date'].strftime('%Y-%m-%d')
        start_time_str = data['start_time'].strftime('%H:%M:%S')
        end_time_str = data['end_time'].strftime('%H:%M:%S')
        
       # Preparar los datos para el registro en Odoo
        odoo_data = {
            'x_studio_tema': data['topic'],
            'x_studio_many2one_field_iphhw': employee_id,
            'x_studio_fecha_sesin': date_str,
            'x_studio_hora_inicial': start_time_str,
            'x_studio_hora_final': end_time_str,
            'x_studio_many2one_field_ftouu': department_id,
            'x_studio_estado': 'ACTIVA',
            'x_studio_modalidad': data.get('mode', ''),
            'x_studio_ubicacin': data.get('location', ''),
            'x_studio_url': data.get('url_reunion', ''),
            'x_studio_asisti': 'Si',
            'x_studio_tipo':data.get('tipo',''),
            'x_studio_fecha_hora_registro': data['registro_datetime'],
            'x_studio_ip_del_registro': data.get('ip_address'),
            'x_studio_user_agent': data.get('user_agent'),
            'x_studio_longitud': data.get('longitude'),
            'x_studio_latitud': data.get('latitude'),
            'x_studio_moderador': data.get('moderator', ''),
            'x_studio_responsable': data.get('in_charge'),
            'x_studio_id_capacitacion': data['capacitacion_id']
        }

        # Verificar que no haya valores None en los datos antes de enviar
        for key, value in odoo_data.items():
            if value is None:
                raise ValueError(f"El campo {key} tiene un valor None, lo que no es permitido en Odoo.")
        
        record_id = models.execute_kw(database, uid, password,
                                      'x_capacitacion_emplead', 'create', [odoo_data])

        # Obtener el nombre del empleado desde el campo `identification_id`
        employee_name = models.execute_kw(database, uid, password,
                                          'hr.employee', 'search_read',
                                          [[['id', '=', employee_id]]],
                                          {'fields': ['identification_id'], 'limit': 1})[0]['identification_id']

        return record_id, employee_name, data.get('url_reunion', '')

    except Exception as e:
        logger.error('Failed to send data to Odoo', exc_info=True)
        return None, None, None



# Función para crear QR de Capacitación
@csrf_exempt
@settings.AUTH.login_required()
def create_capacitacion(request, *, context):
    if request.method == 'POST':
        request.POST = request.POST.copy()
        request.POST['estado'] = 'ACTIVA'
        form = CtrlCapacitacionesForm(request.POST, request.FILES)
        if form.is_valid():
            capacitacion = form.save(commit=False)
            capacitacion.estado = 'ACTIVA'
            capacitacion = form.save()
            
            if capacitacion.tipo in ['Reunión', 'Capacitación']:
                # Procesar archivo PDF si se envió
                if 'archivo_pdf' in request.FILES:
                    print("Se detectó un archivo PDF en request.FILES")  # Debugging
                    pdf_file = request.FILES['archivo_pdf']

                    if pdf_file.content_type == 'application/pdf':
                        filename = f"pdf_evento_{capacitacion.id}_{pdf_file.name}"
                        print(f"Subiendo archivo PDF: {filename}")  # Debugging

                        pdf_url = upload_to_azure_blob(pdf_file, filename)

                        if pdf_url:
                            print(f"PDF subido correctamente: {pdf_url}")  # Debugging
                            capacitacion.pdf_url = pdf_url
                            capacitacion.save()
                        else:
                            print("Error: pdf_url es None")  # Debugging
                            messages.error(request, "Error al subir el archivo PDF a Azure.")
                    else:
                        print(f"Archivo inválido: {pdf_file.content_type}")  # Debugging
                        messages.error(request, "El archivo debe ser un PDF.")
                else:
                    print("No se detectó archivo PDF en request.FILES")  # Debugging

            employee_ids = request.POST.get('employee_names', '').split(',')
            print(f"Empleados seleccionados (POST): {employee_ids}") 
            
                        
            if employee_ids:
                print("Llamando a send_assistants_to_odoo...")  # Confirmar si entra aquí
                send_assistants_to_odoo(capacitacion.id, employee_ids)
                     
            qr_url = f"{apphost}/learn/register/?id={capacitacion.id}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')

            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            capacitacion.qr_base64 = img_base64
            capacitacion.save()
            
            userdata = context['user']
            print('User Data: ', userdata)
            username = userdata.get('name')
            email = userdata.get('preferred_username')
            
            #Log Data
            username = email
            observacion = (f"Creación de la capacitación: {capacitacion.id}")
            id= capacitacion.id
            tipo = "Creación"
            
            #Create Log
            registrar_log_interno(username, observacion, tipo, id)
            

            return HttpResponseRedirect(reverse('details_view', args=[capacitacion.id]))
        else:
            print("El formulario No es válido")
            print(form.errors)
    else:
        form = CtrlCapacitacionesForm()
    return render(request, 'crear_capacitacion.html', {'form': form})

# Función para mostrar lista de Capacitaciones
def list_capacitaciones(request):
    capacitaciones = CtrlCapacitaciones.objects.all()
    return render(request, 'list_capacitaciones.html', {'capacitaciones': capacitaciones})

# Función para registrar asistencia y actualizar registro en Odoo
def registration_view(request, id=None):
    if(id):
        capacitacion_id = id
        capacitacion = get_object_or_404(CtrlCapacitaciones, id=capacitacion_id)
    else:    
        capacitacion_id = request.GET.get('id')
        capacitacion = get_object_or_404(CtrlCapacitaciones, id=capacitacion_id)

    # Formatea la fecha correctamente
    date_str = capacitacion.fecha.strftime('%Y-%m-%d')

    initial_data = {
        'topic': capacitacion.tema,
        'objective': capacitacion.objetivo,
        'department': capacitacion.area_encargada,
        'moderator': capacitacion.moderador,
        'tipo': capacitacion.tipo,
        'date': date_str,
        'start_time': capacitacion.hora_inicial,  # Formato de 24 horas
        'end_time': capacitacion.hora_final,      # Formato de 24 horas
        'mode': capacitacion.modalidad,
        'location': capacitacion.ubicacion,
        'url_reunion': capacitacion.url_reunion,
        'in_charge': capacitacion.responsable,
        'privacidad': capacitacion.privacidad,
        'document_id': ''  # Este campo se llenará por el usuario
    }

    form = RegistrationForm(request.POST or None, initial=initial_data)
    is_active = capacitacion.estado == 'ACTIVA'

    error_message = None  # Inicializa la variable error_message

    if request.method == 'POST' and is_active:
        print('Privacidad: ', capacitacion.privacidad)
        if form.is_valid():
            document_id = form.cleaned_data['document_id']

            try:
                # Verifica la privacidad del evento
                if capacitacion.privacidad == "CERRADA": #priv
                    # Verifica si el documento existe en Odoo
                    employee_id = get_employee_id_by_name(document_id)

                    if not employee_id:
                        error_message = f"No se encontró un empleado con el documento {document_id}. Por favor, verifique los datos."
                    else:
                        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
                        uid = common.authenticate(database, user, password, {})
                        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

                        # Buscar si ya existe un registro del asistente en la capacitación en Odoo
                        existing_records = models.execute_kw(database, uid, password,
                            'x_capacitacion_emplead', 'search_read',
                            [[
                                ['x_studio_id_capacitacion', '=', capacitacion_id],
                                ['x_studio_many2one_field_iphhw', '=', employee_id]
                            ]],
                            {'fields': ['id', 'x_studio_asisti']})
                        
                        timezone = pytz.timezone('America/Bogota')
                        registro_datetime = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
                        user_agent = request.META.get('HTTP_USER_AGENT', '')
                        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
                        latitude = request.POST.get('latitude')
                        longitude = request.POST.get('longitude')
                        
                        if ip_address:
                            ip_address = ip_address.split(',')[0]
                        else:
                            ip_address = request.META.get('REMOTE_ADDR')

                        if existing_records:
                            # Si el registro ya existe, verificar si la asistencia está en "No"
                            record_id = existing_records[0]['id']
                            asistencia_actual = existing_records[0]['x_studio_asisti']

                            if asistencia_actual == 'No':
                                update_data = {
                                    'x_studio_asisti': 'Si',
                                    'x_studio_fecha_hora_registro': registro_datetime,
                                    'x_studio_ip_del_registro': ip_address,
                                    'x_studio_user_agent': user_agent,
                                    'x_studio_longitud': longitude,
                                    'x_studio_latitud': latitude,
                                }
                                
                                models.execute_kw(database, uid, password, 'x_capacitacion_emplead', 'write', [[record_id], update_data])
                                print(f"Asistencia actualizada a 'Sí' para el empleado con documento {document_id}.")
                                
                                employee_name = models.execute_kw(database, uid, password,
                                    'hr.employee', 'search_read',
                                    [[['id', '=', employee_id]]],
                                    {'fields': ['identification_id'], 'limit': 1})[0]['identification_id']
                                
                                encoded_url = quote(capacitacion.url_reunion or 'without-url', safe='')
                                return redirect(reverse('success', kwargs={'employee_name': employee_name, 'url_reunion': encoded_url}))  
                            else:
                                error_message = f"El usuario con documento {document_id} ya ha registrado su asistencia."

                        else:
                            # Redirigir al template de alerta si no está inscrito
                            return render(request, 'no_inscrito.html', {
                                'responsable': capacitacion.responsable, 
                                'capacitacion_id': capacitacion_id,
                                'area_encargada':capacitacion.area_encargada
                                })

                else:  # Si la privacidad es 'ABIERTA', continuar con el flujo normal
                    common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
                    uid = common.authenticate(database, user, password, {})
                    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

                    employee_id = get_employee_id_by_name(document_id)
                    if not employee_id:
                        error_message = f"No se encontró un empleado con el documento {document_id}. Por favor, verifique los datos."
                    else:
                        # Obtener datos adicionales
                        timezone = pytz.timezone('America/Bogota')
                        registro_datetime = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
                        user_agent = request.META.get('HTTP_USER_AGENT', '')
                        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
                        latitude = request.POST.get('latitude')
                        longitude = request.POST.get('longitude')

                        if ip_address:
                            ip_address = ip_address.split(',')[0]
                        else:
                            ip_address = request.META.get('REMOTE_ADDR')

                        # Verificar si ya existe un registro del asistente en la capacitación en Odoo
                        existing_records = models.execute_kw(database, uid, password,
                            'x_capacitacion_emplead', 'search_read',
                            [[
                                ['x_studio_id_capacitacion', '=', capacitacion_id],
                                ['x_studio_many2one_field_iphhw', '=', employee_id]
                            ]],
                            {'fields': ['id', 'x_studio_asisti']})

                        if existing_records:
                            # Si el registro ya existe
                            record_id = existing_records[0]['id']
                            asistencia_actual = existing_records[0]['x_studio_asisti']

                            if asistencia_actual == 'No':
                                update_data = {
                                    'x_studio_asisti': 'Si',
                                    'x_studio_fecha_hora_registro': registro_datetime,
                                    'x_studio_ip_del_registro': ip_address,
                                    'x_studio_user_agent': user_agent,
                                    'x_studio_longitud': longitude,
                                    'x_studio_latitud': latitude,
                                }

                                models.execute_kw(database, uid, password, 'x_capacitacion_emplead', 'write', [[record_id], update_data])
                                print(f"Asistencia actualizada a 'Sí' para el empleado con documento {document_id}.")

                                employee_name = models.execute_kw(database, uid, password,
                                    'hr.employee', 'search_read',
                                    [[['id', '=', employee_id]]],
                                    {'fields': ['identification_id'], 'limit': 1})[0]['identification_id']

                                encoded_url = quote(capacitacion.url_reunion or 'without-url', safe='')
                                return redirect(reverse('success', kwargs={'employee_name': employee_name, 'url_reunion': encoded_url}))
                            else:
                                error_message = f"El usuario con documento {document_id} ya ha registrado su asistencia."
                        else:
                            # Si no existe el registro, crear uno nuevo
                            data = form.cleaned_data
                            data['registro_datetime'] = registro_datetime
                            data['ip_address'] = ip_address
                            data['user_agent'] = user_agent
                            data['latitude'] = latitude
                            data['longitude'] = longitude
                            data['capacitacion_id'] = capacitacion_id
                            data['employee_id'] = employee_id  # Pasar el ID del empleado

                            record_id, employee_name, url_reunion = send_to_odoo(data)
                            if record_id:
                                encoded_url = quote(url_reunion or 'without-url', safe='')
                                return redirect(reverse('success', kwargs={'employee_name': employee_name, 'url_reunion': encoded_url}))
                            else:
                                error_message = "Hubo un problema al enviar los datos a Odoo. Por favor, intente nuevamente."


            except Exception as e:
                logger.error('Error al registrar la asistencia en Odoo:', exc_info=True)
                error_message = "Hubo un problema al verificar los datos en el sistema. Por favor, intente nuevamente."

        else:
            print("El formulario no es válido")
            print(form.errors)

    context = {
        'form': form,
        'is_active': is_active,
        'capacitacion': capacitacion,
        'error_message': error_message
    }

    return render(request, 'registration_form.html', context)

# Vista de Éxito Al Enviar Datos
def success_view(request, employee_name, url_reunion=None):
    decoded_url = unquote(url_reunion) if url_reunion and url_reunion != 'without-url' else None
    context = {
        'employee_name': employee_name,
        'url_reunion': decoded_url  # Usa la URL decodificada o None si no se proporciona
    }
    return render(request, 'success.html', context)

#Vista Detalles de la Capacitación
@settings.AUTH.login_required()
def details_view(request, id, *, context):
    capacitacion = get_object_or_404(CtrlCapacitaciones, id=id)
    
     # Determinar si mostrar ubicación y/o URL de la reunión según la modalidad
    show_url = capacitacion.modalidad == 'VIRTUAL' or capacitacion.modalidad == 'MIXTA'
    show_ubicacion = capacitacion.modalidad == 'PRESENCIAL' or capacitacion.modalidad == 'MIXTA'
    
    context = {
        'topic': capacitacion.tema,
        'department': capacitacion.area_encargada,
        'in_charge': capacitacion.responsable,
        'objective': capacitacion.objetivo,
        'moderator': capacitacion.moderador,
        'date': capacitacion.fecha.strftime('%Y-%m-%d'),
        'start_time': capacitacion.hora_inicial.strftime('%H:%M'),
        'end_time': capacitacion.hora_final.strftime('%H:%M'),
        'modalidad': capacitacion.modalidad, 
        'ubicacion': capacitacion.ubicacion if show_ubicacion else None,  # Condicionalmente según la modalidad
        'url_reunion': capacitacion.url_reunion if show_url else None,  # Condicionalmente según la modalidad
        'qr_url': f"{apphost}/learn/register/?id={capacitacion.id}",
        'qr_base64': capacitacion.qr_base64,
        'topics': capacitacion.temas,
    }
    
    return render(request, 'details_view.html', context)

# Vista Home que muestra todas las capacitaciones
@settings.AUTH.login_required()
def home(request, *, context):
    capacitaciones = CtrlCapacitaciones.objects.all().order_by('estado','-fecha', '-hora_inicial')
    for capacitacion in capacitaciones:
        capacitacion.fecha_formateada = capacitacion.fecha.strftime('%Y-%m-%d')
        capacitacion.hora_inicial_formateada = capacitacion.hora_inicial.strftime('%H:%M')
        capacitacion.hora_final_formateada = capacitacion.hora_final.strftime('%H:%M')
    return render(request, 'home.html', {'capacitaciones': capacitaciones})

#Actualizar Capacitación en Odoo por ID:
def update_odoo_capacitacion (capacitacion):
    try:
        #Conexión Odoo
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
        
        odoo_capacitaciones_ids = models.execute_kw(database, uid, password,
            'x_capacitacion_emplead', 'search',
            [[['x_studio_id_capacitacion', '=', capacitacion.id]]])
        
        
        if odoo_capacitaciones_ids:
            update_data = {
                'x_studio_tema': capacitacion.tema,
                'x_studio_fecha_sesin': capacitacion.fecha.strftime('%Y-%m-%d'),
                'x_studio_hora_inicial': capacitacion.hora_inicial.strftime('%H:%M:%S'),
                'x_studio_hora_final': capacitacion.hora_final.strftime('%H:%M:%S'),
                'x_studio_estado': capacitacion.estado,
                'x_studio_modalidad': capacitacion.modalidad,
                'x_studio_ubicacin': capacitacion.ubicacion or '',
                'x_studio_url': capacitacion.url_reunion or '',
                'x_studio_moderador': capacitacion.moderador,
                'x_studio_tipo': capacitacion.tipo,
                'x_studio_responsable': capacitacion.responsable,
            }
            
            models.execute_kw(database, uid, password,
                              'x_capacitacion_emplead', 'write',
                              [odoo_capacitaciones_ids, update_data])
            
            logger.info(f"Capacitación con ID {capacitacion.id} actualizada en Odoo para {len(odoo_capacitaciones_ids)} registros.")
            
        else:
            logger.warning(f"No se encontró la capacitación con ID {capacitacion.id} en Odoo")
               
        
    except Exception as e:
        logger.error('Error actualizando datos en Odoo', exc_info=True)
        

# Vista para editar una capacitación existente
@csrf_exempt
@settings.AUTH.login_required()
def edit_capacitacion(request, id, *, context):
    capacitacion = get_object_or_404(CtrlCapacitaciones, id=id)
    userdata = context['user']
    print('User Data: ', userdata)
    username = userdata.get('name')
    email = userdata.get('preferred_username')
    
    if request.method == 'POST':
        form = CtrlCapacitacionesForm(request.POST, instance=capacitacion)
        if form.is_valid():
            capacitacion = form.save(commit=False)
            capacitacion.user = username
            form.save()
            
            if capacitacion.tipo in ['Reunión', 'Capacitación']:
                # Procesar archivo PDF si se envió
                if 'archivo_pdf' in request.FILES:
                    print("Se detectó un archivo PDF en request.FILES")  # Debugging
                    pdf_file = request.FILES['archivo_pdf']

                    if pdf_file.content_type == 'application/pdf':
                        filename = f"pdf_evento_{capacitacion.id}_{pdf_file.name}"
                        print(f"Subiendo archivo PDF: {filename}")  # Debugging

                        pdf_url = upload_to_azure_blob(pdf_file, filename)

                        if pdf_url:
                            print(f"PDF subido correctamente: {pdf_url}")  # Debugging
                            capacitacion.pdf_url = pdf_url
                            capacitacion.save()
                        else:
                            print("Error: pdf_url es None")  # Debugging
                            messages.error(request, "Error al subir el archivo PDF a Azure.")
                    else:
                        print(f"Archivo inválido: {pdf_file.content_type}")  # Debugging
                        messages.error(request, "El archivo debe ser un PDF.")
                else:
                    print("No se detectó archivo PDF en request.FILES")  # Debugging
            
            # Obtener los empleados seleccionados del POST
            employee_names = request.POST.get('employee_names', '').split(',')
            print(f"Asistentes seleccionados en edición: {employee_names}")  # Verificar si los datos llegan aquí

            # Llamar a send_assistants_to_odoo después de guardar la capacitación
            if employee_names:
                print("Enviando asistentes a Odoo desde la edición...")
                send_assistants_to_odoo(capacitacion.id, employee_names)
            
            #Log Data
            username = email
            id= capacitacion.id
            
            if capacitacion.estado == 'ACTIVA':
                observacion = f"Modificación de la capacitación: {capacitacion.id}"
                tipo = "Actualización"
            else:
                observacion = f"Cierre de la capacitación: {capacitacion.id}"
                tipo = "Cierre"

            
            #Create Log
            registrar_log_interno(username, observacion, tipo, id)
            #Update Odoo
            update_odoo_capacitacion(capacitacion)
            return redirect('home')
    else:
        form = CtrlCapacitacionesForm(instance=capacitacion)
    return render(request, 'crear_capacitacion.html', {'form': form})


# Vista para ver los usuarios que asistieron a una capacitación
@settings.AUTH.login_required()
def view_assistants(request, id, *, context):
    capacitacion = get_object_or_404(CtrlCapacitaciones, id=id)
    error_message = None
    success_message = None
    
    if request.method == 'POST' and 'image' in request.FILES:
        image_file = request.FILES['image']
        
        
        #Verificar el tamaño de archivo
        if image_file.size > 3 * 1024 *1024:
            error_message = "La imagen excede los 3MB"
        else:
            filename = f"evidencia_{capacitacion.id}_{image_file.name}"
            
            #Cargar imagen a Azure Blob Storage
            image_url = upload_to_azure_blob(image_file, filename)
            
            if image_url:
                # Guardar la URL de la img en el modelo
                capacitacion.image_url = image_url
                capacitacion.save()
                success_message = "Imagen cargada con éxito"
            else:
                error_message = "Erro al cargar la imagen"
        if error_message:
            messages.error(request, error_message)
        if success_message:
            messages.success(request, success_message)
    
    #Remover Acentos
    def remove_accents(input_str):
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        
    capacitacion = get_object_or_404(CtrlCapacitaciones, id=id)
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        assistants = models.execute_kw(database, uid, password,
            'x_capacitacion_emplead', 'search_read',
            [[['x_studio_id_capacitacion', '=',id]]],
            {'fields': ['x_studio_many2one_field_iphhw', 'x_studio_cargo', 'x_studio_nombre_empleado', 'x_studio_departamento_empleado',
                        'x_studio_correo_personal', 'x_studio_correo_corporativo', 'x_studio_asisti']})

        assistant_data_yes = []
        assistant_data_no = []
        
        for assistant in assistants:
            userId = assistant['x_studio_many2one_field_iphhw'][1] if assistant['x_studio_many2one_field_iphhw'] else ''
            jobTitle = assistant.get('x_studio_cargo', '')
            username = assistant.get('x_studio_nombre_empleado','')
            employeeDepartment = assistant.get('x_studio_departamento_empleado','')
            personalEmail = assistant.get('x_studio_correo_personal')
            corporateEmail = assistant.get('x_studio_correo_corporativo') 
            x_studio_asisti = assistant.get('x_studio_asisti','')
            
            
            assistant_data = {
                'userId': userId, 
                'jobTitle': jobTitle, 
                'username':username, 
                'employeeDepartment': employeeDepartment,
                'personalEmail':personalEmail,
                'corporateEmail':corporateEmail
            }

            if x_studio_asisti == 'Si':
                assistant_data_yes.append(assistant_data)
            elif x_studio_asisti == 'No':
                assistant_data_no.append(assistant_data)
        
        #Calcular porcentaje de asistencia:
        total_invitados = capacitacion.total_invitados
        total_asistentes = len(assistant_data_yes)
        tasa_exito = 0
        total_ausentes = total_invitados - total_asistentes
        
        if total_invitados > 0 :
            tasa_exito = (total_asistentes/total_invitados)*100
        
        if request.method == 'POST' and 'images' in request.FILES:
            images = request.FILES.getlist('images')
            total_existing_images = capacitacion.images.count()
            total_images = total_existing_images + len(images)
            
            if total_images > 5:
                messages.error(request, "No puede tener más de 5 imágenes en total")
            else:
                for image_file in images:
                    if image_file.size > 3 * 1024 * 1024:
                        messages.error(request, f"La imagen {image_file.name} excede el tamaño máximo de 3MB.")
                        continue  # Saltar esta imagen y continuar con las demás

                    filename = f"capacitacion_{capacitacion.id}_{image_file.name}"
                    image_url = upload_to_azure_blob(image_file, filename)
                    print('IMAGE-URL: ', image_url)
                    if image_url:
                        EventImage.objects.create(capacitacion=capacitacion, image_url=image_url)
                        messages.success(request, f"La imagen {image_file.name} ha sido cargada exitosamente.")
                    else:
                        messages.error(request, f"No se pudo subir la imagen {image_file.name}.")
                    
        
        # Función para formatear los encabezados
        def format_excel_headers(ws):
            # Color verde #5C9C31 en los encabezados
            fill = PatternFill(start_color="5C9C31", end_color="5C9C31", fill_type="solid")
            # Fuente en negrita
            font = Font(bold=True, color= "FFFFFF")
            # Alineación centrada
            alignment = Alignment(horizontal="center", vertical="center")

            # Aplicar formato a cada celda del encabezado (primera fila)
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=1, column=col)
                cell.fill = fill
                cell.font = font
                cell.alignment = alignment

            # Ajustar automáticamente el ancho de las columnas basado en el texto más largo en todas las filas
            for col_idx in range(1, ws.max_column + 1):
                max_length = 0
                column_letter = get_column_letter(col_idx)  # Obtener la letra de la columna
                for row in ws.iter_rows(min_col=col_idx, max_col=col_idx, min_row=1, max_row=ws.max_row):
                    for cell in row:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))  # Buscar el texto más largo en todas las filas
                adjusted_width = max_length + 5  # Agregar un poco de espacio adicional
                ws.column_dimensions[column_letter].width = adjusted_width  # Ajustar el ancho de la columna

        # Aplicación en el lugar correcto donde se crea el archivo Excel
        if request.GET.get('download') == 'excel':
            # Crear archivo de Excel en memoria
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = remove_accents(f"Datos Asistentes")

            # Escribir encabezados
            ws.append(["Número de Documento", "Nombre", "Cargo", "Área", "Correo Personal", "Correo Corporativo"])

           

            # Agregar datos de los asistentes con manejo de valores vacíos
            for assistant in assistant_data_yes:
                row = [
                    assistant['userId'].strip() if assistant['userId'] else '',
                    assistant['username'].strip() if assistant['username'] else '',
                    assistant['jobTitle'].strip() if assistant['jobTitle'] else '',
                    assistant['employeeDepartment'].strip() if assistant['employeeDepartment'] else '',
                    assistant['personalEmail'].strip() if assistant['personalEmail'] else '',
                    assistant['corporateEmail'].strip() if assistant['corporateEmail'] else ''
                ]
                ws.append(row)
                
            # Formatear archivo
            format_excel_headers(ws)

            # Guardar el archivo en memoria
            output = BytesIO()
            wb.save(output)
            output.seek(0)

            # Generar respuesta HTTP con el archivo
            sanitized_filename = remove_accents(f"Asistentes_{capacitacion.tema}.xlsx")
            response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={sanitized_filename}'

            # Cerrar el workbook antes de enviar la respuesta
            wb.close()
            return response

    except Exception as e:
        logger.error('Failed to fetch assistants from Odoo', exc_info=True)
        assistant_data = []
        tasa_exito = 0

    return render(request, 'view_assistants.html', {
        'capacitacion': capacitacion,
        'assistants_yes': assistant_data_yes,
        'assistants_no': assistant_data_no,
        'total_invitados': total_invitados,
        'tasa_exito': round(tasa_exito, 2), # Cifra redondeada
        'total_ausentes': total_ausentes,
        'error_message': error_message,
        'success_message': success_message
    })
    
# Buscar Empleados en Odoo
def search_employees(request):
    query = request.GET.get('q', '')
    results = []
    
    if query:
        try:
            common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
            uid = common.authenticate(database, user, password, {})
            models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

            employees = models.execute_kw(database, uid, password,
                                          'hr.employee', 'search_read',
                                          [[['name', 'ilike', query]]],  # Filtrar por número de identificación
                                          {'fields': ['id', 'name', 'identification_id'], 'limit': 10})

            results = [{'name': emp['name'], 'identification_id': emp['identification_id']} for emp in employees]

        except Exception as e:
            logger.error('Failed to fetch employees from Odoo', exc_info=True)

    return JsonResponse({'results': results})

#Enviar Asistentes Obligatorios a Odoo
def send_assistants_to_odoo(capacitacion_id, employee_ids):
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
        
        capacitacion = CtrlCapacitaciones.objects.get(id=capacitacion_id)
        
        # Obtener el ID del departamento (area encargada) en Odoo
        department_data = models.execute_kw(database, uid, password,
                                            'hr.department', 'search_read',
                                            [[['name', '=', capacitacion.area_encargada]]],
                                            {'fields': ['id'], 'limit': 1})
        
        if not department_data:
            raise ValueError(f"No se encontró el departamento '{capacitacion.area_encargada}' en Odoo.")
        
        department_id = department_data[0]['id']
        
        
        
       # Loop sobre cada empleado seleccionado
        print('ENVIANDO ASISTENTES A ODOO')
        for name in employee_ids:
            employee_data = models.execute_kw(database, uid, password,
                                              'hr.employee', 'search_read',
                                              [[['name', '=', name]]],
                                              {'fields': ['id'], 'limit': 1})
            if employee_data:
                employee_id = employee_data[0]['id']  # Obtener el ID del empleado en Odoo
                odoo_data = {
                    'x_studio_tema': capacitacion.tema,
                    'x_studio_many2one_field_iphhw': employee_id,  # ID del empleado en Odoo
                    'x_studio_fecha_sesin': capacitacion.fecha.strftime('%Y-%m-%d'),
                    'x_studio_hora_inicial': capacitacion.hora_inicial.strftime('%H:%M:%S'),
                    'x_studio_hora_final': capacitacion.hora_final.strftime('%H:%M:%S'),                                                                                                                       
                    'x_studio_estado':capacitacion.estado,
                    'x_studio_many2one_field_ftouu': department_id,
                    'x_studio_asisti': 'No',  # Marcamos asistencia en 'No'
                    'x_studio_id_capacitacion': capacitacion_id,  # Relacionar con la capacitación
                    'x_studio_responsable': capacitacion.responsable,
                    'x_studio_moderador': capacitacion.moderador,
                    'x_studio_tipo': capacitacion.tipo,
                    'x_studio_modalidad': capacitacion.modalidad,
                    'x_studio_ubicacin': capacitacion.ubicacion or '',
                    'x_studio_url': capacitacion.url_reunion or ''
                }
                
                # Crear el registro de asistente en Odoo
                models.execute_kw(database, uid, password, 'x_capacitacion_emplead', 'create', [odoo_data])

        logger.info(f"Asistentes enviados a Odoo para la capacitación {capacitacion_id}")
        print(f"Asistentes enviados a Odoo para la capacitación {capacitacion_id}") 
    except Exception as e:
        logger.error('Failed to send assistants to Odoo', exc_info=True)