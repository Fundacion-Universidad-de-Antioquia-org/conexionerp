from django.http import JsonResponse
from .utils import odoo_search_read, odoo_update
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from collections import defaultdict

# Vista para traer empleados y actualizar datos
# 1) Obtenemos un logger para este módulo
logger = logging.getLogger(__name__)  # __name__ debe coincidir con 'tu_app.views'
@csrf_exempt
def empleados_list(request):
    # 1) Solo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # 2) Leer filtros de la URL
    compania = request.GET.get('compania')
    estado   = request.GET.get('estado')

    logger.debug(f"[empleados_list] Filtros recibidos – compania={compania!r}, estado={estado!r}")

    # 3) Construir domain con solo compañía y estado
    domain = []
    if compania:
        try:
            domain.append(('company_id', '=', int(compania)))
        except ValueError:
            domain.append(('company_id.name', 'ilike', compania))
    if estado:
        domain.append(('x_studio_estado_empleado', '=', estado))

    logger.debug(f"[empleados_list] Dominio final: {domain!r}")

    # 4) Llamada a Odoo
    empleados = odoo_search_read(
        model='hr.employee',
        domain=domain or None,   # None → todos si no hay filtros
        fields=[
            'id',
            'name',
            'work_email',
            'job_id',
            'work_phone',
            'identification_id',
            'x_studio_estado_empleado'
        ],
        limit=False  
    )

    logger.debug(f"[empleados_list] Odoo devolvió {len(empleados)} empleados")

    return JsonResponse({'empleados': empleados})
@csrf_exempt
def prestadores_list(request):
    domain = []  # ya no metemos supplier_rank ni is_company

    if request.method == 'GET':
        compania     = request.GET.get('compania')
        estado       = request.GET.get('estado')
        prestador_id = request.GET.get('prestador_id')

        if compania:
            try:
                cid = int(compania)
            except ValueError:
                return JsonResponse({"error": "compania debe ser un entero"}, status=400)
            domain.append(['x_studio_company_id', '=', cid])

        if estado:
            # <-- reemplaza 'x_estado' por el nombre REAL de tu campo
            domain.append(['x_studio_estado', '=', estado])

        if prestador_id:
            try:
                pid = int(prestador_id)
            except ValueError:
                return JsonResponse({"error": "prestador_id debe ser un entero"}, status=400)
            domain.append(['id', '=', pid])

    prestadores = odoo_search_read(
        model='x_prestadores_de_servi',
        domain=domain or None,
        fields=[
            'id', 'x_name', 'x_studio_nombre_contratista', 'x_studio_tipo_identificacin',
            'x_studio_cdigo_ciiu', 'x_studio_partner_email'
        ],
        limit=False  
    )
    return JsonResponse({'prestadores': prestadores})
@csrf_exempt
def empleados_conduccion_list(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # dominio fijo para la compañía
    domain = [
        ('company_id.name', '=', 'Programa de Conducción de Vehículos de Transporte Masivo'),  ('x_studio_estado_empleado', '=', 'Activo'),
    ]

    # llamamos a Odoo sin límite de 100
    empleados = odoo_search_read(
        model='hr.employee',
        domain=domain,
        fields=[
            'name',                        # cédula
            'identification_id',           # nombre
            'x_studio_codigo',             # código tripulante
            'x_studio_estado_empleado',    # estado
            'job_title',
            'x_studio_zona_proyecto_metro',# título del puesto
            'x_studio_formacion_conduccion'
        ],
        # prueba primero con False; si falla, cámbialo a 0
        limit=False  
        # o bien limit=0
    )
    # 4) Loguear la cantidad total que vino de Odoo
    total = len(empleados)
    logger.debug(f"[empleados_conduccion_list] Odoo devolvió {total} empleados")

    resultados = [
        {
            'cedula':   emp.get('name'),
            'nombre':   emp.get('identification_id'),
            'Codigo tripulante': emp.get('x_studio_codigo'),
            'estado':   emp.get('x_studio_estado_empleado'),
            'job_title': emp.get('job_title'),
            'zona': emp.get('x_studio_zona_proyecto_metro'),
            'formacion_conduccion': emp.get('x_studio_formacion_conduccion'),
        }
        for emp in empleados
    ]
    return JsonResponse({'empleados': resultados})
@csrf_exempt
def empleado_conduccion_por_codigo(request):
    # 1) Sólo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # 2) Leer el código desde query string
    codigo = request.GET.get('codigo')
    if not codigo:
        return JsonResponse({'error': 'Falta el parámetro "codigo".'}, status=400)
    logger.debug(f"[empleado_conduccion_por_codigo] Filtro recibido – codigo={codigo!r}")

    # 3) Construir dominio: compañía fija + filtro por código
    domain = [
        ('company_id.name', '=', 'Programa de Conducción de Vehículos de Transporte Masivo'), ('x_studio_estado_empleado', '=', 'Activo'),
    ]
    # Intentamos convertir a entero, si falla lo usamos como string
    try:
        domain.append(('x_studio_codigo', '=', int(codigo)))
    except ValueError:
        domain.append(('x_studio_codigo', '=', codigo))
    logger.debug(f"[empleado_conduccion_por_codigo] Domain final: {domain!r}")

    # 4) Llamada a Odoo sin límite de 100
    empleados = odoo_search_read(
        model='hr.employee',
        domain=domain,
        fields=[
            'name',                        # cédula
            'identification_id',           # nombre
            'x_studio_codigo',             # código tripulante
            'x_studio_estado_empleado',    # estado
            'job_title',
            'x_studio_zona_proyecto_metro',# título del puesto
            'x_studio_formacion_conduccion'# título del puesto
        ],
        limit=False  # o limit=0 si tu wrapper lo prefiere
    )
    total = len(empleados)
    logger.debug(f"[empleado_conduccion_por_codigo] Odoo devolvió {total} registros")

    # 5) Mapear al JSON de respuesta
    resultados = [
        {
            'cedula':              emp.get('name'),
            'nombre':              emp.get('identification_id'),
            'Codigo tripulante':   emp.get('x_studio_codigo'),
            'estado':              emp.get('x_studio_estado_empleado'),
            'job_title':           emp.get('job_title'),
            'zona': emp.get('x_studio_zona_proyecto_metro'),
            'formacion_conduccion': emp.get('x_studio_formacion_conduccion'),

        }
        for emp in empleados
    ]

    # 6) Devolver JSON
    return JsonResponse({'empleados': resultados})
"""@csrf_exempt
def contratos_list(request):
    # 1) Sólo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # 2) Leer parámetros
    cedula    = request.GET.get('cedula')    # la cédula a buscar
    estado_in = request.GET.get('estado')    # “Activo” o “Retirado”

    # 3) Construir domain
    domain = []
    if cedula:
        # filtramos por el campo related.identification_id directamente
        domain.append([
            'x_studio_many2one_field_4arFu.name',
            '=',
            cedula
        ])
    if estado_in:
        e = estado_in.strip().capitalize()
        if e not in ('Activo', 'Retirado'):
            return JsonResponse(
                {'error': 'Parámetro estado inválido; use "Activo" o "Retirado".'},
                status=400
            )
        domain.append(['x_studio_estado_contrato', '=', e])

    # 4) Definir campos según el estado
    fields_activo = [
        'x_name',
        'x_studio_tipo_contrato',
        'x_studio_fecha_inicio_contrato',
        'x_studio_fecha_fin_contrato',
        'x_studio_estado_contrato',
        'x_studio_salario_contrato',
        'x_studio_nmero_contrato',
        'x_studio_nombre_empleado',
        'x_studio_many2one_field_jcBPU',
    ]
    fields_retirado = [
        'x_name',
        'x_studio_tipo_contrato',
        'x_studio_fecha_inicio_contrato',
        'x_studio_fecha_vencimiento_contrato',
        'x_studio_estado_contrato',
        'x_studio_many2one_field_kEZoK',
        'x_studio_salario_contrato',
        'x_studio_nmero_contrato',
        'x_studio_nombre_empleado',
        'x_studio_many2one_field_jcBPU',
    ]

    if estado_in:
        # si piden activo/retirado, devolvemos sólo el set correspondiente
        fields = fields_activo if e == 'Activo' else fields_retirado
    else:
        # si no piden estado, devolvemos todos los campos (unión)
        fields = list({*fields_activo, *fields_retirado})

    # 5) Llamada a Odoo
    try:
        contratos = odoo_search_read(
            model='x_contratos_empleados',
            domain=domain or None,
            fields=fields
        )
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)

    return JsonResponse({'contratos': contratos})
"""


@csrf_exempt
def contratos_list(request):
    # 1) Sólo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # 2) Parámetros
    cedula    = request.GET.get('cedula')
    estado_in = request.GET.get('estado')   # “Activo” | “Retirado”
    logger.debug("Filtros recibidos → cedula=%r, estado=%r", cedula, estado_in)

    # 3) Paso 1: resolver la cédula a un ID de hr.employee
    emp_domain = [['name', '=', cedula]] if cedula else []
    emp_rec = odoo_search_read(
        model='hr.employee',
        domain=emp_domain or None,
        fields=['id']
    )
    emp_ids = [e['id'] for e in emp_rec]
    if cedula and not emp_ids:
        logger.debug("No existe empleado con cédula %r", cedula)
        return JsonResponse({'contratos': []})

    # 4) Paso 2: construir dominio para contratos
    domain = []
    # filtro por el many2one en base al ID
    domain.append(['x_studio_many2one_field_4arFu', 'in', emp_ids])
    logger.debug("Filtro por employee_id resolvido: %r", domain[-1])

    # filtro por estado (exacto “Activo”/“Retirado”)
    if estado_in:
        e = estado_in.strip().capitalize()
        if e not in ('Activo', 'Retirado'):
            return JsonResponse(
                {'error': 'Parámetro estado inválido; use "Activo" o "Retirado".'},
                status=400
            )
        domain.append(['x_studio_estado_contrato', '=', e])
        logger.debug("Filtro por estado: %r", domain[-1])

    logger.debug("Dominio completo para contratos: %r", domain)

    # 5) Elegir campos según estado
    fields_activo = [
        'x_name',
        'x_studio_tipo_contrato',
        'x_studio_fecha_inicio_contrato',
        'x_studio_fecha_fin_contrato',
        'x_studio_estado_contrato',
        'x_studio_salario_contrato',
        'x_studio_nmero_contrato',
        'x_studio_nombre_empleado',
        'x_studio_many2one_field_jcBPU',
    ]
    fields_retirado = [
        'x_name',
        'x_studio_tipo_contrato',
        'x_studio_fecha_inicio_contrato',
        'x_studio_fecha_vencimiento_contrato',
        'x_studio_estado_contrato',
        'x_studio_many2one_field_kEZoK',
        'x_studio_salario_contrato',
        'x_studio_nmero_contrato',
        'x_studio_nombre_empleado',
        'x_studio_many2one_field_jcBPU',
    ]

    if estado_in:
        fields = fields_activo if e == 'Activo' else fields_retirado
    else:
        # unión sin duplicados
        fields = list({*fields_activo, *fields_retirado})

    logger.debug("Campos solicitados: %r", fields)

    # 6) Llamada final a Odoo
    try:
        contratos = odoo_search_read(
            model='x_contratos_empleados',
            domain=domain,
            fields=fields
        )
        logger.debug("Odoo devolvió %d contratos", len(contratos))
    except Exception as exc:
        logger.exception("Error en odoo_search_read")
        return JsonResponse({'error': str(exc)}, status=500)

    return JsonResponse({'contratos': contratos})
def estados_basicos_list(request):
    estados = odoo_search_read(
        model='x_contratos_empleados',
        fields=['id', 'name', 'state', 'active']
    )
    return JsonResponse({'estados': estados})

# Vista para traer salarios

@csrf_exempt
def empleados_y_sus_hijos_activos(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # 1. Consultar hijos con empleados activos
    hijos = odoo_search_read(
        model='x_hijos',
        domain=[('x_studio_estado_empleado', '=', 'Activo')],
        fields=[
            'x_studio_many2one_field_XctqN',        # Cédula (Many2One, se extrae el valor [1])
            'x_studio_nombre_empleado_1',           # Nombre empleado
            'x_name',                               # Identificación hijo
            'x_studio_nombre',
            'x_studio_fecha_de_nacimiento',
            'x_studio_gnero',
            'x_studio_edad'
        ],
        limit=False
    )

    from collections import defaultdict
    agrupado = defaultdict(lambda: {'cedula': '', 'nombre': '', 'hijos': []})

    for hijo in hijos:
        cedula_field = hijo.get('x_studio_many2one_field_XctqN')  # [ID, valor]
        cedula = cedula_field[1] if isinstance(cedula_field, list) and len(cedula_field) > 1 else ''

        nombre = hijo.get('x_studio_nombre_empleado_1')
        if not cedula:
            continue

        agrupado[cedula]['cedula'] = cedula
        agrupado[cedula]['nombre'] = nombre
        agrupado[cedula]['hijos'].append({
            'x_name': hijo.get('x_name'),
            'x_studio_nombre': hijo.get('x_studio_nombre'),
            'x_studio_fecha_de_nacimiento': hijo.get('x_studio_fecha_de_nacimiento'),
            'x_studio_gnero': hijo.get('x_studio_gnero'),
            'x_studio_edad': hijo.get('x_studio_edad'),
        })

    return JsonResponse({'empleados': list(agrupado.values())}, safe=False)
def salarios_list(request):
    salarios = odoo_search_read(
        model='hr.contract',
        fields=['id', 'employee_id', 'wage']
    )
    return JsonResponse({'salarios': salarios})

# Vista para traer estudios

def estudios_list(request):
    estudios = odoo_search_read(
        model='hr.education',
        fields=['id', 'employee_id', 'name', 'date_start', 'date_end', 'level']
    )
    return JsonResponse({'estudios': estudios})

# Vista para actualizar datos de empleado

@csrf_exempt
def actualizar_empleado(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        empleado_id = data.get('id')
        valores = data.get('valores', {})
        resultado = odoo_update('hr.employee', [empleado_id], valores)
        return JsonResponse({'resultado': resultado})
    return JsonResponse({'error': 'Método no permitido'}, status=405)
