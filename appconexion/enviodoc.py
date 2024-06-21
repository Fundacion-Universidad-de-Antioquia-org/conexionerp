import os
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
site_id = os.getenv('SITE_ID_GESTIONTIC')
library_name = os.getenv('LIBRARY_NAME')



"""Este módulo contiene funciones para sincronizar datos de Odoo con SharePoint ."""
"""def obtener_archivo_odoo():

    common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
    uid = common.authenticate(database, user, password, {})
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    registros = models.execute_kw(database, uid, password, 'hr.employee', 'search_read', 
                                  [[('x_studio_pendiente_sincronizacion', '=', 'Si')]],
                                  {'fields': ['x_studio_fotocopia_cedula', 'name']})
    if registros and 'x_studio_fotocopia_cedula' in registros[0]:
        archivo_base64 = registros[0]['x_studio_fotocopia_cedula']
        nombre_archivo = f"{registros[0]['name']}.pdf" 
        print("archivo obtenido con exito", registros )# Asume que quieres guardar como PDF
        return archivo_base64, nombre_archivo
    print("No se encontraron empleados pendientes de sincronización en Odoo.")
    return None, None"""
    
    


def obtener_access_token_doc():
    url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    data = {
        'client_id': client_id,
        'scope': scope,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        token_response = response.json()
        access_token = token_response.get('access_token')
        if access_token:
            print("Token de acceso obtenido exitosamente:", access_token)
            return access_token
        else:
            print("Token de acceso no encontrado en la respuesta.")
    except requests.exceptions.HTTPError as e:
        print("HTTP Error:", e.response.status_code, e.response.text)
    except requests.exceptions.RequestException as e:
        print("Request Error:", str(e))
    except Exception as e:
        print("Unexpected Error:", str(e))
    return None


"""def cargar_archivo_a_sharepoint(archivo_binario, nombre_archivo, access_token):
    create_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{library_name}/root:/{nombre_archivo}:/content"
    print('URL creada:', create_url)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",
    }
    try:
        response = requests.put(create_url, headers=headers, data=archivo_binario)
        response.raise_for_status()
        response_json = response.json()
        file_id = response_json.get('id')
        print(f"Archivo cargado correctamente con ID: {file_id}")
        return file_id
    except requests.exceptions.HTTPError as e:
        print(f"Error al cargar el archivo: {e.response.status_code} {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return None"""

def cargar_archivo_a_sharepoint(archivo_binario, nombre_archivo, access_token):
    create_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{library_name}/items/root:/{nombre_archivo}:/content"
    print("URL:", create_url)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",
    }
    response = requests.put(create_url, headers=headers, data=archivo_binario)
    if response.status_code in [200, 201]:
        file_data = response.json()
        file_id = file_data.get('id')
        print("Archivo cargado correctamente con ID:", file_id)
        return file_id
    else:
        print("Error al cargar el archivo:", response.status_code, response.text)
        return None

# Actualizar metadatos de un archivo en SharePoint
def actualizar_metadatos_sharepoint(file_id, access_token):
    metadata = {
        "fields": {
            "Soporte": "PAPEL"
        }
    }
    print("Datos de envío:", metadata)
    update_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{library_name}/items/{file_id}/listItem/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.patch(update_url, headers=headers, json=metadata)
    print("Estado de la respuesta:", response.status_code)
    print("Cuerpo de la respuesta:", response.text)  # Mejor visibilidad del error

    if response.status_code == 200:
        print("Metadatos actualizados correctamente.")
        return True
    else:
        print("Error al actualizar metadatos:", response.status_code, response.text)
        return False





    """def cargar_archivo_a_sharepoint(archivo_binario, nombre_archivo, access_token):
    print('library name', library_name)
    
    create_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{library_name}/items/root:/{nombre_archivo}:/content"
  #https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{library_name}/{nombre_archivo}:/content
    print('Url creada', create_url)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",
    }
    try:
        response = requests.put(create_url, headers=headers, data=archivo_binario)
        response.raise_for_status()
        print("Archivo cargado correctamente.")
    except requests.exceptions.HTTPError as e:
        print("Error al cargar el archivo:", e.response.status_code, e.response.text)
    except requests.exceptions.RequestException as e:
        print("Request Error:", str(e))
    except Exception as e:
        print("Unexpected Error:", str(e))
    finally:
        print("Response Status Code:", response.status_code)
        print("Response Text:", response.text)
    return response
"""


