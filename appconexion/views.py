

from .odoo_sync import obtener_registros_pendientes, sincronizar_con_sharepoint, obtener_access_token
from .odoo_prestadores import obtener_access_token_presta, sincronizar_con_sharepoint_presta,obtener_registros_pendientes_presta
from .enviodoc import obtener_access_token_doc, cargar_archivo_a_sharepoint, actualizar_metadatos_sharepoint
from django.http import JsonResponse
from .odoo_sync import obtener_access_token, obtener_registros_pendientes, sincronizar_con_sharepoint
# Create your views here.
from dotenv import load_dotenv
import time
import logging



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

logger = logging.getLogger(__name__)

def sync_view_doc(request):
    file_path = os.path.join(os.path.dirname(__file__), 'files', 'Directorio-Prueba2.csv')
    logger.info(f"Intentando acceder al archivo en: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error("Archivo local no encontrado.")
        return JsonResponse({"error": "Archivo local no encontrado."}, status=404)

    access_token = obtener_access_token_doc()
    if not access_token:
        logger.error("No se pudo obtener el token de acceso.")
        return JsonResponse({"error": "No se pudo obtener el token de acceso."}, status=500)

    with open(file_path, 'rb') as file:
        archivo_binario = file.read()

    file_id = cargar_archivo_a_sharepoint(archivo_binario, 'Directorio-Prueba2.csv', access_token)
    if file_id:
        logger.info(f"Archivo cargado con ID: {file_id}")
        time.sleep(5)  # Espera 5 segundos antes de actualizar metadatos
        if actualizar_metadatos_sharepoint(file_id, access_token):
            return JsonResponse({"success": "Archivo cargado y metadatos actualizados correctamente en SharePoint."}, status=200)
        else:
            logger.error("Falló la actualización de metadatos.")
            return JsonResponse({"error": "Falló la actualización de metadatos"}, status=500)
    else:
        logger.error("Falló la carga del archivo.")
        return JsonResponse({"error": "Falló la carga del archivo"}, status=500)

"""def sync_view_doc(request):
    #file_path = os.path.join(os.path.dirname(__file__), 'files', 'Directorio-Prueba.csv')
    #print("Intentando acceder al archivo en:", file_path)
    # Datos de la columna a actualizar, por ejemplo: {'Title': 'Nuevo Título', 'CustomColumn': 'Valor'}
    file_path = os.path.join(os.path.dirname(__file__), 'files', 'Directorio-Prueba2.csv')
    print("Intentando acceder al archivo en:", file_path)
    if not os.path.exists(file_path):
        return JsonResponse({"error": "Archivo local no encontrado."}, status=404)

    access_token = obtener_access_token_doc()
    if not access_token:
        return JsonResponse({"error": "No se pudo obtener el token de acceso."}, status=500)

    with open(file_path, 'rb') as file:
        archivo_binario = file.read()

    file_id = cargar_archivo_a_sharepoint(archivo_binario, 'Directorio-Prueba2.csv', access_token)
    if file_id:
        print(f"Archivo cargado con ID: {file_id}")
        time.sleep(5)  # Espera 5 segundos antes de actualizar metadatos
        # Datos de la columna a actualizar, asegurándote de incluir todos los campos obligatorios
        #metadata = {
        #"Nombredelexpediente": "1111-Angie Prueba",
        #"Soporte": "PAPEL"  # Suponiendo que este es otro campo obligatorio.
        #}
        if actualizar_metadatos_sharepoint(file_id,access_token):
            return JsonResponse({"success": "Archivo cargado y metadatos actualizados correctamente en SharePoint."}, status=200)
        else:
            return JsonResponse({"error": "Falló la actualización de metadatos"}, status=500)
    else:
        return JsonResponse({"error": "Falló la carga del archivo"}, status=500)"""


"""    column_data = {
        'Nombredelexpediente': '1020483722-Angie Cardona',
        'CustomColumn': 'Valor Específico'
    }
    if not os.path.exists(file_path):
        return JsonResponse({"error": "Archivo local no encontrado."}, status=404)

    access_token = obtener_access_token_doc()
    if not access_token:
        return JsonResponse({"error": "No se pudo obtener el token de acceso."}, status=500)

    with open(file_path, 'rb') as file:
        archivo_binario = file.read()

    response = cargar_archivo_a_sharepoint(archivo_binario, 'Directorio-Prueba.csv', column_data, access_token)
    if response.status_code in [200, 201]:
        return JsonResponse({"success": "Archivo cargado correctamente en SharePoint."}, status=200)
    else:
        return JsonResponse({"error": "Falló la carga del archivo", "details": response.text}, status=response.status_code)"""


