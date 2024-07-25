from django.http import JsonResponse
import logging
from app_sync import sync_empleados_comunicaciones, sync_prestadores_comunicaciones
from app_file_management.views import * #ajustar agregando las tareas
from app_task_sync import sync_tasks_comunicaciones
from app_pdf_management import * #ajustar agregando las tareas
from app_file_management.views import * #ajustar agregando las tareas

logger = logging.getLogger(__name__)

def execute_multiple_tasks(request):
    response_data = {
        'sync_empleados_comunicaciones': None,
        'sync_prestadores_comunicaciones': None,
        'sync_tasks_comunicaciones': None,
    }

    try:
        result, status = sync_empleados_comunicaciones()
        response_data['sync_empleados_comunicaciones'] = result
    except Exception as e:
        logger.error(f"Error syncing employees: {e}")
        response_data['sync_empleados_comunicaciones'] = {"error": str(e)}

    try:
        result = sync_prestadores_comunicaciones()
        response_data['sync_prestadores_comunicaciones'] = result
    except Exception as e:
        logger.error(f"Error handling file operations: {e}")
        response_data['sync_prestadores_comunicaciones'] = {"error": str(e)}

    try:
        result = sync_tasks_comunicaciones()
        response_data['sync_tasks'] = result
    except Exception as e:
        logger.error(f"Error syncing tasks: {e}")
        response_data['sync_tasks'] = {"error": str(e)}

    return JsonResponse(response_data)