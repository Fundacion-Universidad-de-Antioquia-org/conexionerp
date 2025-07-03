import xmlrpc.client
from django.conf import settings
import os
from dotenv import load_dotenv


load_dotenv()
ODOO_URL = os.getenv("HOST")
ODOO_DB =  os.getenv("DATABASE")
ODOO_USERNAME =  os.getenv("ODOO_USER")
ODOO_PASSWORD =  os.getenv("PASSWORD")


def get_odoo_connection():
    """
    Retorna los objetos necesarios para interactuar con Odoo via XML-RPC.
    """
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    return uid, models


def odoo_search_read(model, domain=None, fields=None, limit=100):
    """
    Realiza una búsqueda y lectura en un modelo de Odoo.
    """
    uid, models = get_odoo_connection()
    if domain is None:
        domain = []
    if fields is None:
        fields = []
    return models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        model, 'search_read',
        [domain], {'fields': fields, 'limit': limit}
    )


def odoo_update(model, ids, values):
    """
    Actualiza registros en un modelo de Odoo.
    """
    uid, models = get_odoo_connection()
    return models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        model, 'write',
        [ids, values]
    )
