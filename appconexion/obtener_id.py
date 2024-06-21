import requests
import os
from dotenv import load_dotenv

load_dotenv()
database = os.getenv("DATABASE")
user = os.getenv("USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
tenant_id = os.getenv('TENANT_ID')
client_id = os.getenv('CLIENT_ID')
client_secret  = os.getenv('CLIENT_SECRET')
scope = os.getenv('SCOPE')
site_url  = os.getenv('SITE_ID_GESTIONTIC')
library_name = os.getenv('LIBRARY_NAME')

# Endpoint para obtener el token
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
token_data = {
    'client_id': client_id,
    'scope': 'https://graph.microsoft.com/.default',
    'client_secret': client_secret,
    'grant_type': 'client_credentials',
}

# Función para obtener el token de acceso

# Función para obtener el token de acceso
def get_access_token():
    response = requests.post(token_url, data=token_data)
    response.raise_for_status()  # Asegúrate de que la solicitud fue exitosa
    return response.json().get('access_token', None)

# Función para obtener el ID del sitio de SharePoint
def get_site_id(base_url, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    endpoint = f"https://graph.microsoft.com/v1.0/sites/{base_url}"
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json().get('id', None)

# Función para listar las bibliotecas de documentos en el sitio
def list_libraries(site_id, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json().get('value', [])

# Flujo principal
def main():
    try:
        access_token = get_access_token()
        if access_token:
            print("Token de acceso obtenido:", access_token)
        else:
            print("No se pudo obtener el token de acceso.")
            return

        site_id = get_site_id(site_url, access_token)
        if site_id:
            print("ID del sitio obtenido:", site_id)
        else:
            print("No se pudo obtener el ID del sitio.")
            return

        libraries = list_libraries(site_id, access_token)
        if libraries:
            print("Bibliotecas disponibles:")
            for library in libraries:
                print(f"ID: {library['id']}, Nombre: {library['name']}")
        else:
            print("No se encontraron bibliotecas.")
    
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err.response.status_code} {err.response.text}")
    except Exception as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    main()