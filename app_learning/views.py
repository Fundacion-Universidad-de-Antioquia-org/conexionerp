import qrcode
import pytz
import logging
import base64
import openpyxl
import xmlrpc.client
import unicodedata
import os
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CtrlCapacitacionesForm, RegistrationForm
from .models import CtrlCapacitaciones
from django.http import HttpResponseRedirect
from django.urls import reverse
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote
from urllib.parse import unquote
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
database = os.getenv("DATABASE")
user = os.getenv("ODOO_USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
apphost = os.getenv('APP_HOST')

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
def get_employee_id_by_name(employee_name):
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        employees = models.execute_kw(database, uid, password,
            'hr.employee', 'search_read',
            [[['name', '=', employee_name]]],
            {'fields': ['id', 'name'], 'limit': 1})
        
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

        employee_data = models.execute_kw(database, uid, password,
                                          'hr.employee', 'search_read',
                                          [[['name', '=', data['document_id']]]],
                                          {'fields': ['id', 'name'], 'limit': 1})

        if not employee_data:
            raise ValueError(f"Employee with name '{data['document_id']}' not found in Odoo")

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
        logger.error('Failed to send data to Odoo:', e)
        return None, None, None



# Función para crear QR de Capacitación
def create_capacitacion(request):
    
    if request.method == 'POST':
        form = CtrlCapacitacionesForm(request.POST)
        if form.is_valid():
            capacitacion = form.save(commit=False)
            capacitacion.estado = 'ACTIVA'
            capacitacion = form.save()
                     
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

            return HttpResponseRedirect(reverse('details_view', args=[capacitacion.id]))
    else:
        form = CtrlCapacitacionesForm()
    return render(request, 'crear_capacitacion.html', {'form': form})

# Función para mostrar lista de Capacitaciones
def list_capacitaciones(request):
    capacitaciones = CtrlCapacitaciones.objects.all()
    return render(request, 'list_capacitaciones.html', {'capacitaciones': capacitaciones})


# Función para registrar asistencia y actualizar registro en Odoo
def registration_view(request):
    capacitacion_id = request.GET.get('id')
    capacitacion = get_object_or_404(CtrlCapacitaciones, id=capacitacion_id)

    # Formatea la fecha correctamente
    date_str = capacitacion.fecha.strftime('%Y-%m-%d')

    initial_data = {
        'topic': capacitacion.tema,
        'objective': capacitacion.objetivo,
        'department': capacitacion.area_encargada,
        'moderator': capacitacion.moderador,
        'date': date_str,
        'start_time': capacitacion.hora_inicial,  # Formato de 24 horas
        'end_time': capacitacion.hora_final,      # Formato de 24 horas
        'mode': capacitacion.modalidad,
        'location': capacitacion.ubicacion,
        'url_reunion': capacitacion.url_reunion,
        'in_charge': capacitacion.responsable,
        'document_id': ''  # Este campo se llenará por el usuario
    }

    form = RegistrationForm(request.POST or None, initial=initial_data)
    is_active = capacitacion.estado == 'ACTIVA'

    error_message = None  # Inicializa la variable error_message
    
    print("Valor de in_charge: ", request.POST.get('in_charge'))

    if request.method == 'POST' and is_active:
        
        if form.is_valid():
            
            document_id = form.cleaned_data['document_id']

            try:
                # Verifica si el documento existe en Odoo
                employee_id = get_employee_id_by_name(document_id)
                
                if not employee_id:
                    error_message = f"No se encontró un empleado con el documento {document_id}. Por favor, verifique los datos."
                else:
                    common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
                    uid = common.authenticate(database, user, password, {})
                    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

                    # Buscar registros en Odoo para evitar duplicados
                    existing_records = models.execute_kw(database, uid, password,
                        'x_capacitacion_emplead', 'search_read',
                        [[
                            ['x_studio_tema', '=', capacitacion.tema],
                            ['x_studio_fecha_sesin', '=', capacitacion.fecha.strftime('%Y-%m-%d')],
                            ['x_studio_many2one_field_iphhw', '=', employee_id]
                        ]],
                        {'fields': ['id']})

                    if existing_records:
                        error_message = f"El usuario con documento {document_id} ya está registrado en esta capacitación."
                    else:
                        #Obtener fecha y hora actual
                        timezone = pytz.timezone('America/Bogota')
                        registro_datetime = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
                        user_agent = request.META.get('HTTP_USER_AGENT', '')
                        
                        # Obtener la dirección IP del cliente
                        ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
                        
                        #Capturar Ubicación
                        latitude = request.POST.get('latitude')
                        longitude = request.POST.get('longitude')

                        
                        if ip_address:
                            ip_address = ip_address.split(',')[0]
                        else:
                            ip_address = request.META.get('REMOTE_ADDR')
                            
                        url_reunion = form.cleaned_data.get('url_reunion', '')
                        
                        if not url_reunion or url_reunion.lower() == 'none':
                            url_reunion = 'without-url'  # Establece un valor por defecto
                            
                        # Si no existe duplicado, procede a crear el registro en Odoo
                        data = form.cleaned_data
                        data['registro_datetime'] = registro_datetime
                        data['ip_address'] = ip_address
                        data['user_agent'] = user_agent
                        data['latitude'] = latitude
                        data['longitude'] = longitude
                        data['capacitacion_id']= capacitacion_id
                        record_id, employee_name, url_reunion = send_to_odoo(data)
                        if record_id:
                            # Redirigir a la vista de éxito con el nombre del empleado
                            encoded_url = quote(url_reunion, safe='')
                            return redirect(reverse('success', kwargs={'employee_name': employee_name, 'url_reunion': encoded_url}))
                        else:
                            error_message = "Hubo un problema al enviar los datos a Odoo. Por favor, intente nuevamente."

            except Exception as e:
                logger.error('Failed to verify or register assistant in Odoo', exc_info=True)
                error_message = "Hubo un problema al verificar los datos en el sistema. Por favor, intente nuevamente."
        
        else:
            print("El formulario no es válido")
            print(form.errors)

    context = {
        'form': form,
        'is_active': is_active,
        'capacitacion': capacitacion,
        'error_message': error_message  # Incluye error_message en el contexto
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
def details_view(request, id):
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
        'qr_base64': capacitacion.qr_base64
    }
    
    return render(request, 'details_view.html', context)

# Vista Home que muestra todas las capacitaciones
def home(request):
    capacitaciones = CtrlCapacitaciones.objects.all()
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
        
        odoo_capacitacion = models.execute_kw(database, uid, password,
            'x_capacitacion_emplead', 'search_read',
            [[['x_studio_id_capacitacion', '=', capacitacion.id]]],
            {'fields': ['id'], 'limit': 1})
        
        if odoo_capacitacion:
            odoo_capacitacion_id = odoo_capacitacion[0]['id']
            
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
                'x_studio_responsable': capacitacion.responsable
            }
            
            models.execute_kw(database, uid, password,
                              'x_capacitacion_emplead', 'write',
                              [[odoo_capacitacion_id], update_data])
            
            logger.info(f"Capacitación con ID {capacitacion.id} actualizada en Odoo")
            
        else:
            logger.warning(f"No se encontró la capacitación con ID {capacitacion.id} en Odoo")
               
        
    except Exception as e:
        logger.error('Error actualizando datos en Odoo', exc_info=True)
        

# Vista para editar una capacitación existente
def edit_capacitacion(request, id):
    capacitacion = get_object_or_404(CtrlCapacitaciones, id=id)
    if request.method == 'POST':
        form = CtrlCapacitacionesForm(request.POST, instance=capacitacion)
        if form.is_valid():
            capacitacion = form.save(commit=False)
            form.save()
            update_odoo_capacitacion(capacitacion)
            return redirect('home')
    else:
        form = CtrlCapacitacionesForm(instance=capacitacion)
    return render(request, 'crear_capacitacion.html', {'form': form})


# Vista para ver los usuarios que asistieron a una capacitación
def view_assistants(request, id):
    
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
                        'x_studio_correo_personal', 'x_studio_correo_corporativo']})

        assistant_data = []
        for assistant in assistants:
            userId = assistant['x_studio_many2one_field_iphhw'][1] if assistant['x_studio_many2one_field_iphhw'] else ''
            jobTitle = assistant.get('x_studio_cargo', '')
            username = assistant.get('x_studio_nombre_empleado','')
            employeeDepartment = assistant.get('x_studio_departamento_empleado','')
            personalEmail = assistant.get('x_studio_correo_personal')
            corporateEmail = assistant.get('x_studio_correo_corporativo') 
            
            
            assistant_data.append({'userId': userId, 
                                   'jobTitle': jobTitle, 
                                   'username':username, 
                                   'employeeDepartment': employeeDepartment,
                                   'personalEmail':personalEmail,
                                   'corporateEmail':corporateEmail})
        
        #Calcular porcentaje de asistencia:
        total_invitados = capacitacion.total_invitados
        total_asistentes = len(assistant_data)
        tasa_exito = 0
        
        if total_invitados > 0 :
            tasa_exito = (total_asistentes/total_invitados)*100
        
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
            for assistant in assistant_data:
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
        'assistants': assistant_data,
        'tasa_exito': round(tasa_exito, 2) # Cifra redondeada
    })