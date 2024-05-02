# En algún archivo de tu aplicación (por ejemplo, utils.py)

import requests

def realizar_solicitud_http():
    try:
        # Configura la URL que deseas abrir
        url = "https://app-conexionerp-prod-001.azurewebsites.net/appconexion/sincronizar"  # Reemplaza con tu URL

        # Realiza la solicitud HTTP
        response = requests.get(url)

        if response.status_code == 200:
            print(f"Respuesta recibida: {response.status_code}")
        else:
            print(f"Error al realizar la solicitud: {response.status_code}")

    except Exception as ex:
        print(f"Error: {ex}")
