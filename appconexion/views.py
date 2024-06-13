

from .odoo_sync import obtener_registros_pendientes, sincronizar_con_sharepoint, obtener_access_token
from .odoo_prestadores import obtener_access_token_presta, sincronizar_con_sharepoint_presta,obtener_registros_pendientes_presta
from django.http import JsonResponse
from .odoo_sync import obtener_access_token, obtener_registros_pendientes, sincronizar_con_sharepoint
# Create your views here.
from dotenv import load_dotenv


load_dotenv()
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
from django.http import JsonResponse
import os

def show_env(request):
    data = {
        'Database': os.getenv("DATABASE"),
        'User': os.getenv("USER"),
        'Tenant ID': os.getenv("TENANT_ID"),
        'Client ID': os.getenv("CLIENT_ID"),
        'Client Secret': os.getenv("CLIENT_SECRET"),  # Cuidado con exponer esto públicamente
        'Scope': os.getenv("SCOPE"),
        'Site ID': os.getenv("SITE_ID"),
        'List Name': os.getenv("LIST_NAME"),
    }
    return JsonResponse(data)
def sync_view_presta(request):
    # Intentar obtener un token de acceso
    try:
        access_token = obtener_access_token_presta()
        if not access_token:
            return JsonResponse({"error": "Fallo al obtener el token de acceso"}, status=500)
    except Exception as e:
        # En caso de que algo falle al obtener el token
        return JsonResponse({"error": "Error al obtener el token de acceso: {}".format(str(e))}, status=500)

    # Intentar obtener registros pendientes
    try:
        registros = obtener_registros_pendientes_presta()
        if not registros:
            return JsonResponse({"info": "No hay registros pendientes de sincronización"}, status=200)

        # Intentar sincronizar con SharePoint
        resultado = sincronizar_con_sharepoint_presta(registros, access_token)
        return JsonResponse({"success": "Sincronización completada", "detalles": resultado}, status=200)
    except Exception as e:
        # En caso de que algo falle durante la obtención de registros o la sincronización
        return JsonResponse({"error": "Error durante la sincronización: {}".format(str(e))}, status=500)