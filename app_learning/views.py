import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CtrlCapacitacionesForm, RegistrationForm
from .models import CtrlCapacitaciones
from django.http import HttpResponseRedirect
from django.urls import reverse
from io import BytesIO
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
apphost = os.getenv('APP_HOST')

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
        logger.error('Failed to fetch department ID from Odoo' + e, exc_info=True)
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

         # Convertir fechas a cadenas
        date_str = data['date'].strftime('%Y-%m-%d')
        start_time_str = data['start_time'].strftime('%H:%M:%S')
        end_time_str = data['end_time'].strftime('%H:%M:%S')
        
        odoo_data = {
            'x_studio_tema': data['topic'],
            'x_studio_many2one_field_iphhw': employee_id,
            'x_studio_fecha_sesin': date_str,
            'x_studio_hora_inicial': start_time_str,
            'x_studio_hora_final': end_time_str,
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

            return HttpResponseRedirect(reverse('details_view') + f'?id={capacitacion.id}')
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
    
    initial_data = {
        'topic': capacitacion.tema,
        'objective': capacitacion.objetivo,
        'department': capacitacion.area_encargada,
        'moderator': capacitacion.moderador,
        'date': capacitacion.fecha,
        'start_time': capacitacion.hora_inicial,
        'end_time': capacitacion.hora_final,
        'document_id': ''  # Este campo se llenará por el usuario
    }
    
    form = RegistrationForm(request.POST or None, initial=initial_data)
    is_active = capacitacion.estado == 'ACTIVA'
    
    if request.method == 'POST' and is_active:
        if form.is_valid():
            document_id = form.cleaned_data['document_id']

            try:
                common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
                uid = common.authenticate(database, user, password, {})
                models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

                # Buscar el asistente en Odoo
                assistants = models.execute_kw(database, uid, password,
                    'x_capacitacion_emplead', 'search_read',
                    [[
                        ['x_studio_tema', '=', capacitacion.tema],
                        ['x_studio_fecha_sesin', '=', capacitacion.fecha.strftime('%Y-%m-%d')],
                        ['x_studio_hora_inicial', '=', capacitacion.hora_inicial.strftime('%H:%M:%S')],
                        ['x_studio_many2one_field_iphhw', '=', document_id]  # Aquí se hace la comparación con el document_id
                    ]],
                    {'fields': ['x_studio_many2one_field_iphhw']})
                
                if assistants:
                    # Si ya está registrado, limpiar el campo document_id pero mantener los demás datos
                    form.data = form.data.copy()
                    form.data['document_id'] = ''
                    error_message = f"El usuario con documento {document_id} ya está registrado en esta capacitación."
                    context = {
                        'form': form,
                        'is_active': is_active,
                        'capacitacion': capacitacion,
                        'error_message': error_message
                    }
                    return render(request, 'registration_form.html', context)
                else:
                    # Si no está registrado, proceder con el registro
                    data = form.cleaned_data
                    send_to_odoo(data)
                    return redirect('success')

            except Exception as e:
                logger.error('Failed to verify assistant in Odoo', exc_info=True)
                error_message = "Hubo un problema al verificar los datos en el sistema. Por favor, intente nuevamente."
                context = {
                    'form': form,
                    'is_active': is_active,
                    'capacitacion': capacitacion,
                    'error_message': error_message
                }
                return render(request, 'registration_form.html', context)

    context = {
        'form': form,
        'is_active': is_active,
        'capacitacion': capacitacion
    }
    
    return render(request, 'registration_form.html', context)


# Vista de Éxito Al Enviar Datos
def success_view(request):
    return render(request, 'success.html')

#Vista Detalles de la Capacitación
def details_view(request, id):
    capacitacion = get_object_or_404(CtrlCapacitaciones, id=id)
    
    context = {
        'topic': capacitacion.tema,
        'department': capacitacion.area_encargada,
        'objective': capacitacion.objetivo,
        'moderator': capacitacion.moderador,
        'date': capacitacion.fecha.strftime('%Y-%m-%d'),
        'start_time': capacitacion.hora_inicial.strftime('%H:%M'),
        'end_time': capacitacion.hora_final.strftime('%H:%M'),
        'qr_url': f"{apphost}/learn/register/?id={capacitacion.id}",
        'qr_base64': capacitacion.qr_base64
    }
    
    return render(request, 'details_view.html', context)

# Vista Home que muestra todas las capacitaciones
def home(request):
    capacitaciones = CtrlCapacitaciones.objects.all()
    for capacitacion in capacitaciones:
        capacitacion.fecha_formateada = capacitacion.fecha.strftime('%Y-%m-%d')
        
        
    return render(request, 'home.html', {'capacitaciones': capacitaciones})

# Vista para editar una capacitación existente
def edit_capacitacion(request, id):
    capacitacion = get_object_or_404(CtrlCapacitaciones, id=id)
    if request.method == 'POST':
        form = CtrlCapacitacionesForm(request.POST, instance=capacitacion)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = CtrlCapacitacionesForm(instance=capacitacion)
    return render(request, 'crear_capacitacion.html', {'form': form})

# Vista para ver los usuarios que asistieron a una capacitación
def view_assistants(request, id):
    capacitacion = get_object_or_404(CtrlCapacitaciones, id=id)
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        assistants = models.execute_kw(database, uid, password,
            'x_capacitacion_emplead', 'search_read',
            [[
                ['x_studio_tema', '=', capacitacion.tema],
                ['x_studio_fecha_sesin', '=', capacitacion.fecha.strftime('%Y-%m-%d')],
                ['x_studio_hora_inicial', '=', capacitacion.hora_inicial.strftime('%H:%M:%S')]
            ]],
            {'fields': ['x_studio_many2one_field_iphhw']})
        
        assistant_names = [assistant['x_studio_many2one_field_iphhw'][1] for assistant in assistants]
        
    except Exception as e:
        logger.error('Failed to fetch assistants from Odoo', exc_info=True)
        assistant_names = []

    return render(request, 'view_assistants.html', {'capacitacion': capacitacion, 'assistants': assistant_names})
