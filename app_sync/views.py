from django.http import JsonResponse
from .utils import (
    fetch_x_bancos,
    fetch_x_eps,
    fetch_x_arl,
    fetch_x_afp,
    fetch_x_banco,
    fetch_x_centro_costos,
    fetch_x_talla_camisa,
    fetch_x_talla_calzado,
    fetch_x_talla_pantalon,
    fetch_x_paises,
    fetch_x_cesantias

)

def odoo_data_endpoint(request):
    """
    Endpoint que junta la información de los distintos modelos en Odoo:
    - Municipios (x_bancos)
    - EPS (x_eps)
    - ARL (x_arl)
    - AFP (x_afp)
    - Banco (x_banco)
    - Centro Costos (x_centro_costos)
    - Talla Camisa (x_talla_camisa)
    - Talla Calzado (x_talla_calzado)
    - Talla Pantalón (x_talla_pantalon)
    """
    response_data = {
        "paises":fetch_x_paises(),
        "municipios": fetch_x_bancos(),
        "eps": fetch_x_eps(),
        "arl": fetch_x_arl(),
        "afp": fetch_x_afp(),
        "banco": fetch_x_banco(),
        "centro_costos": fetch_x_centro_costos(),
        "talla_camisa": fetch_x_talla_camisa(),
        "talla_calzado": fetch_x_talla_calzado(),
        "talla_pantalon": fetch_x_talla_pantalon(),
        "cesantias":fetch_x_cesantias(),
    }
    return JsonResponse(response_data)
