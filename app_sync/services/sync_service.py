from app_integrations.services.odoo_service import obtener_registros_pendientes, sincronizar_con_sharepoint, obtener_access_token
from app_integrations.services.odoo_service import obtener_access_token_presta, sincronizar_con_sharepoint_presta, obtener_registros_pendientes_presta
from app_integrations.services.token_service import obtener_access_token_doc, cargar_archivo_a_sharepoint, actualizar_metadatos_sharepoint
import os
import time
import logging

logger = logging.getLogger(__name__)

def sync_employees():
    try:
        access_token = obtener_access_token()
        if not access_token:
            return {"error": "Fallo al obtener el token de acceso"}, 500
    except Exception as e:
        return {"error": f"Error al obtener el token de acceso: {str(e)}"}, 500

    try:
        registros = obtener_registros_pendientes()
        if not registros:
            return {"info": "No hay registros pendientes de sincronización"}, 200

        resultado = sincronizar_con_sharepoint(registros, access_token)
        return {"success": "Sincronización completada", "detalles": resultado}, 200
    except Exception as e:
        return {"error": f"Error durante la sincronización: {str(e)}"}, 500

def sync_prestadores():
    try:
        access_token = obtener_access_token_presta()
        if not access_token:
            return {"error": "Fallo al obtener el token de acceso"}, 500
    except Exception as e:
        return {"error": f"Error al obtener el token de acceso: {str(e)}"}, 500

    try:
        registros = obtener_registros_pendientes_presta()
        if not registros:
            return {"info": "No hay registros pendientes de sincronización"}, 200

        resultado = sincronizar_con_sharepoint_presta(registros, access_token)
        return {"success": "Sincronización completada", "detalles": resultado}, 200
    except Exception as e:
        return {"error": f"Error durante la sincronización: {str(e)}"}, 500

def sync_documents():
    file_path = os.path.join(os.path.dirname(__file__), 'files', 'Directorio-Prueba2.csv')
    logger.info(f"Intentando acceder al archivo en: {file_path}")

    if not os.path.exists(file_path):
        logger.error("Archivo local no encontrado.")
        return {"error": "Archivo local no encontrado."}, 404

    access_token = obtener_access_token_doc()
    if not access_token:
        logger.error("No se pudo obtener el token de acceso.")
        return {"error": "No se pudo obtener el token de acceso."}, 500

    with open(file_path, 'rb') as file:
        archivo_binario = file.read()

    file_id = cargar_archivo_a_sharepoint(archivo_binario, 'Directorio-Prueba2.csv', access_token)
    if file_id:
        logger.info(f"Archivo cargado con ID: {file_id}")
        time.sleep(5)  # Espera 5 segundos antes de actualizar metadatos
        if actualizar_metadatos_sharepoint(file_id, access_token):
            return {"success": "Archivo cargado y metadatos actualizados correctamente en SharePoint."}, 200
        else:
            logger.error("Falló la actualización de metadatos.")
            return {"error": "Falló la actualización de metadatos"}, 500
    else:
        logger.error("Falló la carga del archivo.")
        return {"error": "Falló la carga del archivo"}, 500
