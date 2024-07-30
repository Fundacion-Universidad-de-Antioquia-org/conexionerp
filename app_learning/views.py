import qrcode
from django.shortcuts import render, redirect
from .forms import CtrlCapacitacionesForm, RegistrationForm
from .models import CtrlCapacitaciones
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from io import BytesIO
from urllib.parse import unquote, urlencode
import xmlrpc.client
import os
from dotenv import load_dotenv
import logging
import base64


logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
database = os.getenv("DATABASE")
user = os.getenv("ODOO_USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")

#Función para obtener el ID del departamento
def get_department_id(department_name):
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        # Buscar el ID del departamento por nombre
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

#Función para obtener el ID del empleado por Nombre:
def get_employee_id_by_name(employee_name):
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        # Buscar el ID del empleado por su nombre
        employees = models.execute_kw(database, uid, password,
            'hr.employee', 'search_read',
            [[['name', '=', employee_name]]],
            {'fields': ['id', 'name'], 'limit': 1})
        
        if employees:
            print(f"Employee found: {employees[0]}")
            return employees[0]['id']
        else:
            print(f"No employee found with name: {employee_name}")
            return None
    
    except Exception as e:
        logger.error('Failed to fetch employee ID from Odoo', exc_info=True)
        return None

#Función para enviar
def send_to_odoo(data):
    
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        # Obtener el ID del departamento
        department_id = get_department_id(data['department'])
        if not department_id:
            raise ValueError(f"Department '{data['department']}' not found in Odoo")

        # Obtener el ID del empleado por nombre
        employee_id = get_employee_id_by_name(data['document_id'])
        if not employee_id:
            raise ValueError(f"Employee with name '{data['document_id']}' not found in Odoo")

        # Preparar los datos para enviar a Odoo
        odoo_data = {
            'x_studio_tema': data['topic'],
            'x_studio_many2one_field_iphhw': employee_id,
            'x_studio_fecha_sesin': data['date'],
            'x_studio_hora_inicial': data['start_time'],
            'x_studio_hora_final': data['end_time'],
            'x_studio_many2one_field_ftouu': department_id,
            'x_studio_estado': 'ACTIVA',  # Asumiendo que siempre es ACTIVA, puedes cambiar esto si es necesario
            'x_studio_moderador': data['moderator'],
            'x_studio_asisti': 'Si'
        }

        # Crear el registro en Odoo
        record_id = models.execute_kw(database, uid, password,
                                      'x_capacitacion_emplead', 'create', [odoo_data])

        logger.debug(f'Record created in Odoo with ID: {record_id}')
        return record_id

    except Exception as e:
        logger.error('Failed to send data to Odoo', exc_info=True)
        return None

#Función para crear QR de Capacitación
import base64

def create_capacitacion(request):
    if request.method == 'POST':
        form = CtrlCapacitacionesForm(request.POST)
        if form.is_valid():
            capacitacion = form.save()
            qr_data = {
                'topic': capacitacion.tema,
                'department': capacitacion.area_encargada,
                'moderator': capacitacion.moderador,
                'date': capacitacion.fecha,
                'start_time': capacitacion.hora_inicial,
                'end_time': capacitacion.hora_final
            }
            query_string = urlencode(qr_data)
            qr_url = f"http://127.0.0.1:8000/learn/register/?{query_string}"

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
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Guardar la imagen QR temporalmente
            qr_dir = os.path.join('static', 'qr_codes')
            if not os.path.exists(qr_dir):
                os.makedirs(qr_dir)
            
            qr_path = os.path.join(qr_dir, f"{capacitacion.id}.png")
            with open(qr_path, 'wb') as f:
                f.write(buffer.getvalue())

            # Redirigir a la vista de detalles con el QR y la información
            return HttpResponseRedirect(reverse('details_view') + f'?{query_string}&qr_path={qr_path}')
    else:
        form = CtrlCapacitacionesForm()
    return render(request, 'crear_capacitacion.html', {'form': form})


#Función para mostrar lista de Capacitaciones
def list_capacitaciones(request):
    capacitaciones = CtrlCapacitaciones.objects.all()
    return render(request, 'list_capacitaciones.html', {'capacitaciones': capacitaciones})

#Función para registrar asistencia y actualizar registro en Odoo
def registration_view(request):
    initial_data = {}
    if request.GET:
        initial_data = {
            'topic': request.GET.get('topic', ''),
            'department': request.GET.get('department', ''),
            'moderator': request.GET.get('moderator', ''),
            'date': request.GET.get('date', ''),
            'start_time': request.GET.get('start_time', ''),
            'end_time': request.GET.get('end_time', '')
        }
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Procesa los datos en form.cleaned_data
            topic = form.cleaned_data['topic']
            department = form.cleaned_data['department']
            moderator = form.cleaned_data['moderator']
            date = form.cleaned_data['date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            document_id = form.cleaned_data['document_id']
            
            # Crear diccionario con los datos
            data = {
                'topic': topic,
                'department': department,
                'moderator': moderator,
                'date': date.strftime('%Y-%m-%d'),
                'start_time': start_time.strftime('%H:%M:%S'),
                'end_time': end_time.strftime('%H:%M:%S'),
                'document_id': document_id
            }
            
            # Enviar datos a Odoo
            send_to_odoo(data)
            
            # Redirigir a la vista de éxito
            return redirect('success')
    else:
        form = RegistrationForm(initial=initial_data)

    return render(request, 'registration_form.html', {'form': form})

#Vista de Éxito
def success_view(request):
    return render(request, 'success.html')

def details_view(request):
    context = {
        'topic': request.GET.get('topic', ''),
        'department': request.GET.get('department', ''),
        'moderator': request.GET.get('moderator', ''),
        'date': request.GET.get('date', ''),
        'start_time': request.GET.get('start_time', ''),
        'end_time': request.GET.get('end_time', ''),
        'qr_url': f"http://127.0.0.1:8000/learn/register/?{request.GET.urlencode()}",
        'qr_path': request.GET.get('qr_path', '')
    }


    return render(request, 'details_view.html', context)

