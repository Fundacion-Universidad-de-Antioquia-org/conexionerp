from django.http import JsonResponse
from app_sync.services.sync_service import sync_employees, sync_prestadores, sync_documents


def sync_empleados_comunicaciones(request):
    result, status = sync_employees()
    return JsonResponse(result, status=status)

def sync_prestadores_comunicaciones(request):
    result, status = sync_prestadores()
    return JsonResponse(result, status=status)

def sync_view_doc(request):
    result, status = sync_documents()
    return JsonResponse(result, status=status)
