

from .odoo_sync import obtener_registros_pendientes, sincronizar_con_sharepoint, obtener_access_token

from django.http import JsonResponse
from .odoo_sync import obtener_access_token, obtener_registros_pendientes, sincronizar_con_sharepoint
# Create your views here.
def sync_view(request):
    # Intentar obtener un token de acceso
    try:
        access_token = obtener_access_token()
        if not access_token:
            return JsonResponse({"error": "Fallo al obtener el token de acceso"}, status=500)
    except Exception as e:
        # En caso de que algo falle al obtener el token
        return JsonResponse({"error": "Error al obtener el token de acceso: {}".format(str(e))}, status=500)

    # Intentar obtener registros pendientes
    try:
        registros = obtener_registros_pendientes()
        if not registros:
            return JsonResponse({"info": "No hay registros pendientes de sincronización"}, status=200)

        # Intentar sincronizar con SharePoint
        resultado = sincronizar_con_sharepoint(registros, access_token)
        return JsonResponse({"success": "Sincronización completada", "detalles": resultado}, status=200)
    except Exception as e:
        # En caso de que algo falle durante la obtención de registros o la sincronización
        return JsonResponse({"error": "Error durante la sincronización: {}".format(str(e))}, status=500)
