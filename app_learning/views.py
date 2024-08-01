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
            print(f"Employee found: {employees[0]}")
            return employees[0]['id']
        else:
            print(f"No employee found with name: {employee_name}")
            return None
    
    except Exception as e:
        logger.error('Failed to fetch employee ID from Odoo', exc_info=True)
        return None

# Función para enviar datos a Odoo
def send_to_odoo(data):
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        department_id = get_department_id(data['department'])
        if not department_id:
            raise ValueError(f"Department '{data['department']}' not found in Odoo")

        employee_id = get_employee_id_by_name(data['document_id'])
        if not employee_id:
            raise ValueError(f"Employee with name '{data['document_id']}' not found in Odoo")

        odoo_data = {
            'x_studio_tema': data['topic'],
            'x_studio_many2one_field_iphhw': employee_id,
            'x_studio_fecha_sesin': data['date'],
            'x_studio_hora_inicial': data['start_time'],
            'x_studio_hora_final': data['end_time'],
            'x_studio_many2one_field_ftouu': department_id,
            'x_studio_estado': 'ACTIVA',
            'x_studio_moderador': data['moderator'],
            'x_studio_asisti': 'Si'
        }

        record_id = models.execute_kw(database, uid, password,
                                      'x_capacitacion_emplead', 'create', [odoo_data])

        logger.debug(f'Record created in Odoo with ID: {record_id}')
        return record_id

    except Exception as e:
        logger.error('Failed to send data to Odoo', exc_info=True)
        return None

# Función para crear QR de Capacitación
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
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            img_base64 = img_base64.replace('\n', '')  # Elimina cualquier salto de línea

            return HttpResponseRedirect(reverse('details_view') + f'?{query_string}&qr_base64={img_base64}')
    else:
        form = CtrlCapacitacionesForm()
    return render(request, 'crear_capacitacion.html', {'form': form})

# Función para mostrar lista de Capacitaciones
def list_capacitaciones(request):
    capacitaciones = CtrlCapacitaciones.objects.all()
    return render(request, 'list_capacitaciones.html', {'capacitaciones': capacitaciones})

# Función para registrar asistencia y actualizar registro en Odoo
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
            topic = form.cleaned_data['topic']
            department = form.cleaned_data['department']
            moderator = form.cleaned_data['moderator']
            date = form.cleaned_data['date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            document_id = form.cleaned_data['document_id']
            
            data = {
                'topic': topic,
                'department': department,
                'moderator': moderator,
                'date': date.strftime('%Y-%m-%d'),
                'start_time': start_time.strftime('%H:%M:%S'),
                'end_time': end_time.strftime('%H:%M:%S'),
                'document_id': document_id
            }
            
            send_to_odoo(data)
            
            return redirect('success')
    else:
        form = RegistrationForm(initial=initial_data)

    return render(request, 'registration_form.html', {'form': form})

# Vista de Éxito Al Enviar Datos
def success_view(request):
    return render(request, 'success.html')

#Vista Detalles de la Capacitación
def details_view(request):
    context = {
        'topic': request.GET.get('topic', ''),
        'department': request.GET.get('department', ''),
        'moderator': request.GET.get('moderator', ''),
        'date': request.GET.get('date', ''),
        'start_time': request.GET.get('start_time', ''),
        'end_time': request.GET.get('end_time', ''),
        'qr_url': f"http://127.0.0.1:8000/learn/register/?{request.GET.urlencode()}",
        'qr_base64': request.GET.get('qr_base64', '').replace(' ', '+')  # Asegúrate de que no haya espacios
    }

    return render(request, 'details_view.html', context)
