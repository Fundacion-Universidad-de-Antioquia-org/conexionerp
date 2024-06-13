import os
import time
from urllib.parse import quote
import xmlrpc.client

import requests
from dotenv import load_dotenv

#cambio
load_dotenv()
database = os.getenv("DATABASE")
user = os.getenv("USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
tenant_id = os.getenv('TENANT_ID')
client_id = os.getenv('CLIENT_ID')
client_secret  = os.getenv('CLIENT_SECRET')
scope = os.getenv('SCOPE')
site_id = os.getenv('SITE_ID')
list_name = os.getenv('LIST_NAME_PRESTA')

"""Este módulo contiene funciones para sincronizar datos de Odoo con SharePoint ."""
def obtener_registros_pendientes_presta():
    """Esta función trae los registros desde Odoo."""
    # Conexión al servicio de autenticación de Odoo
    common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
    uid = common.authenticate(database, user, password, {})
    # Conexión al servicio de objetos de Odoo para password operaciones en los modelos
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    # Búsqueda de empleados pendientes de sincronización
    registros = models.execute_kw(database, uid, password,
        'x_prestadores_de_servi', 'search_read',
        [[('x_studio_pendiente_sincronizacion', '=', 'Si')]],
        {'fields': ['x_studio_nombre_contratista','x_name', 'x_studio_company_id',
         'x_studio_partner_email', 'x_studio_fecha_de_nacimiento', 'x_studio_estado', 'x_studio_fecha_ingreso']})
    if registros:
        print("Empleados pendientes de sincronización obtenidos con éxito desde Odoo.")
        print("registros", registros)
        return registros
    print("No se encontraron empleados pendientes de sincronización en Odoo.")
    return None
def obtener_access_token_presta():
    """Esta función obtiene el token de Sharepoint."""
    url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    data = {
        'client_id': client_id,
        'scope': scope,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(url, data=data, timeout=10)
    response.raise_for_status()
    token_response = response.json()
    access_token = token_response.get('access_token')
    if access_token:
        print("Token de acceso obtenido exitosamente:", access_token)
        return response.json().get('access_token')
    print("Error al obtener el token de acceso:", token_response)
    return None     # Esto lanzará un error si la solicitud falla
def verificar_si_existe_presta( x_name, access_token):
    """Esta función valida los registros de Odoo si ya existen el sharepoint."""
    headers = {"Authorization": f"Bearer {access_token}",
               "Content-Type": "application/json", 
               "Prefer": "HonorNonIndexedQueriesWarningMayFailRandomly" }
    search_url = (
    f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_name}"
    f"/items?$filter=fields/field_1 eq '{quote(x_name)}'&$top=100"
    )
    response = requests.get(search_url, headers=headers, timeout=10)
    if response.status_code == 200 and response.json()['value']:
        item = response.json()['value'][0]
        item_id = item['id']
        etag = item.get('@odata.etag')
        print("id", item_id)
        print("etag:",etag)
        return item_id, etag
    return None, None
def marcar_registro_como_sincronizado_presta(x_name):
    """Esta función Ingresa a la BD de Odoo y actualiza el registro."""
    if not x_name:
        print("No se proporcionó un nombre de empleado para marcar como sincronizado.")
        return
    # Conexión al servicio de autenticación de Odoo
    common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
    uid = common.authenticate(database, user, password, {})
    # Conexión al servicio de objetos de Odoo para realizar operaciones en los modelos
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    # Busca el ID del empleado basado en el 'name' (nombre) proporcionado
    employee_id = models.execute_kw(database, uid, password,
                                    'x_prestadores_de_servi', 'search',
                                    [[('x_name', '=', x_name)]])
    if not employee_id:
        print(f"No se encontró el empleado con nombre {x_name} para marcar como sincronizado.")
        return
    # Marca el registro como sincronizado
    response = models.execute_kw(database, uid, password,
        'x_prestadores_de_servi', 'write',
        [employee_id, {'x_studio_pendiente_sincronizacion': 'No'}],
        {'context': {'skip_sync': True}})
    if response:
        print(f"Empleado {x_name} marcado como sincronizado con éxito.")
    else:
        print("Error al actualizar el registro.")
def sincronizar_con_sharepoint_presta(registros, access_token):
    """Esta función cumple con controlar y ejecutar el metodo eliminar y crear."""
    for registro in registros:
        x_studio_nombre_contratista = registro['x_studio_nombre_contratista'] if registro['x_studio_nombre_contratista'] else None
        x_name = registro['x_name'] if registro['x_name'] else None
        _, x_studio_company_id = registro['x_studio_company_id'] if registro['x_studio_company_id'] else None
        x_studio_partner_email = registro['x_studio_partner_email'] if registro['x_studio_partner_email'] else None
        x_studio_estado = registro['x_studio_estado'] if registro['x_studio_estado']  else None
        x_studio_fecha_de_nacimiento = registro['x_studio_fecha_de_nacimiento']
        birthday2 = f"{x_studio_fecha_de_nacimiento}T00:00:00Z" if x_studio_fecha_de_nacimiento else None
        x_studio_fecha_ingreso = registro['x_studio_fecha_ingreso']
        fecha_ingreso=f"{x_studio_fecha_ingreso}T00:00:00Z" if x_studio_fecha_ingreso else None
        #print("Fecha de ingreso formateada:", fecha_de_ingreso)  # Debug para ver la fecha formateada
        item_id, etag = verificar_si_existe_presta(x_name, access_token)
        # Lógica para manejar el estado del registro
        if x_studio_estado == "Activo" and item_id:
            eliminado_exitosamente = eliminar_registro_presta(item_id, etag, access_token, site_id, list_name)
            crear_registro_en_sharepoint_presta(x_name, x_studio_nombre_contratista, x_studio_company_id,
                                        x_studio_partner_email,x_studio_estado,birthday2,fecha_ingreso,
                                         access_token,
                                        site_id, list_name)
            marcar_registro_como_sincronizado_presta(x_name)
        elif x_studio_estado == "Activo":
            print(f"Ingrese a registrar a lista: {x_name}")
            print("Fecha de ingreso enviar antes:", fecha_ingreso)
            crear_registro_en_sharepoint_presta(x_name, x_studio_nombre_contratista, x_studio_company_id,
                                        x_studio_partner_email,x_studio_estado,birthday2,fecha_ingreso,
                                         access_token,
                                        site_id, list_name)
            if crear_registro_en_sharepoint_presta:
                marcar_registro_como_sincronizado_presta(x_name)
        elif x_studio_estado == "Retirado" and item_id:
            print(f"Ingrese a eliminarlo a lista: {x_name}")
            eliminado_exitosamente = eliminar_registro_presta(item_id, etag, access_token, site_id, list_name)
            if eliminado_exitosamente:
                marcar_registro_como_sincronizado_presta(x_name)
def eliminar_registro_presta(item_id, etag, access_token, site_id, list_name):
    """Esta función elimina los registros de sharepoint por ID."""
    delete_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_name}/items/{item_id}"
    delete_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "If-Match": etag  # Necesario para la eliminación
    }
    delete_response = requests.delete(delete_url, headers=delete_headers, timeout=10)
    delete_response.raise_for_status()# Esto lanzará una excepción si la solicitud falla
    print(f"Registro eliminado con éxito: {item_id}")
def crear_registro_en_sharepoint_presta(x_name, x_studio_nombre_contratista, x_studio_company_id,
                                        x_studio_partner_email,x_studio_estado,birthday2,fecha_ingreso,
                                         access_token,
                                        site_id, list_name):
    """Esta función crea los registros de sharepoint."""
    create_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_name}/items"
    create_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    print("Fecha de ingreso enviar despues:", fecha_ingreso)  # D
    payload = {
        "fields": {
            "Title": x_studio_estado,
            "field_1": x_name,
            "field_2": x_studio_nombre_contratista,
            "field_3": x_studio_partner_email,
            "field_4": birthday2,
            "field_5": fecha_ingreso,
            "field_6": x_studio_company_id,
        }
    }
    try:
        create_response = requests.post(create_url, headers=create_headers, json=payload, timeout=10)
        create_response.raise_for_status()
        print(f"Sincronizado con éxito: {x_name}")
        return True
    except requests.exceptions.HTTPError as err:
        print("HTTP Error:", err.response.status_code)
        print("Error al crear el registro. Respuesta completa:", err.response.text)
        return False
    except requests.exceptions.RequestException as e:
        print("Error en la solicitud:", str(e))
        return False
"""    create_response = requests.post(create_url, headers=create_headers, json=payload, timeout=10)
    print("Estado del envio", create_response.status_code)
    print("Error al crear el registro. Respuesta completa:", create_response.text)
    if create_response.status_code in [200, 201]:
        print(f"Sincronizado con éxito: {name}")
        return True
    elif create_response.status_code == 500:
        enviar_solicitud_con_reintento(create_url, create_headers, payload)
        if create_response.status_code in [200, 201]:
            print(f"Sincronizado con éxito después del reintento: {name}")
            return True
        else:
            print("Error al crear el registro. Respuesta completa:")
            print(create_response.text)
            return False
            print(f"Error al sincronizar después del reintento: {name}")"""
def enviar_solicitud_con_reintento_presta(url, headers, payload, max_reintentos=5):
    """Esta función reintenta los registros que fallan."""
    espera = 2
    for reintento in range(max_reintentos):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 500:
                print(f"Error 500 detectado, reintento {reintento + 1} de {max_reintentos}. Esperando {espera} segundos.")
                time.sleep(espera)
                espera *= 2# Aumenta el tiempo de espera para el próximo intento
            else:
                print(f"Error {e.response.status_code}: {e.response.text}")
                raise
    raise Exception("Se alcanzó el máximo número de reintentos sin éxito para crear el registro en SharePoint.")
def clear_sharepoint_list_presta(access_token, site_id, list_name):
    """Esta función elimina todos los registros de sharepoint."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    get_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_name}/items'
    response = requests.get(get_url, headers=headers, timeout=10)
    if response.status_code == 200:
        items = response.json().get('value', [])
        if not items:
            print("La lista ya está vacía.")
        batch_size = 20
        for i in range(0, len(items), batch_size):
            batch = {"requests": []}
            for item in items[i:i+batch_size]:
                batch["requests"].append({
                    "id": str(item["id"]),
                    "method": "DELETE",
                    "url": f"/sites/{site_id}/lists/{list_name}/items/{item['id']}"
                })
            batch_url = "https://graph.microsoft.com/v1.0/$batch"
            batch_response = requests.post(batch_url, headers=headers, json=batch, timeout=10)
            if batch_response.status_code == 200:
                print(f"Elementos del lote {i//batch_size + 1} eliminados exitosamente.")
            else:
                print(f"Error al eliminar elementos del lote {i//batch_size + 1}: {batch_response.text}")
    else:
        print("Error al obtener elementos de la lista:", response.text)
