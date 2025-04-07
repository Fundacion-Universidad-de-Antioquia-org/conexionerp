import os
import xmlrpc.client
import logging
from dotenv import load_dotenv

load_dotenv()

# Variables de entorno
database = os.getenv("DATABASE")
user = os.getenv("ODOO_USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def get_odoo_uid():
    """Autentica y retorna el uid de Odoo"""
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        return uid
    except Exception as e:
        logger.error("Error autenticando en Odoo", exc_info=True)
        return None


def fetch_x_paises():
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        return models.execute_kw(
            database, uid, password,
            'x_paises', 'search_read',
            [[]],
            {'fields': ['x_name', 'id']}
        )
    except Exception as e:
        logger.error("Error al obtener x_paises", exc_info=True)
        return []
def fetch_x_cesantias():
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        return models.execute_kw(
            database, uid, password,
            'x_cesantias', 'search_read',
            [[]],
            {'fields': ['x_name', 'id']}
        )
    except Exception as e:
        logger.error("Error al obtener x_paises", exc_info=True)
        return []
def fetch_x_bancos():
    """
    Modelo MUNICIPIOS: x_bancos
    Se obtiene x_name, x_studio_departamento y id. 
    Se concatena x_name con x_studio_departamento (ej: "MEDELLIN - ANTIOQUIA").
    """
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        records = models.execute_kw(
            database, uid, password,
            'x_bancos', 'search_read',
            [[]],
            {'fields': ['x_name', 'x_studio_departamento', 'id']}
        )
        for record in records:
            name = record.get('x_name', '')
            departamento = record.get('x_studio_departamento', '')
            if departamento:
                record['x_name'] = f"{name} - {departamento}"
        return records
    except Exception as e:
        logger.error("Error al obtener x_bancos", exc_info=True)
        return []

def fetch_x_eps():
    """Modelo EPS: x_eps"""
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        return models.execute_kw(
            database, uid, password,
            'x_eps', 'search_read',
            [[]],
            {'fields': ['x_name', 'id']}
        )
    except Exception as e:
        logger.error("Error al obtener x_eps", exc_info=True)
        return []

def fetch_x_arl():
    """Modelo ARL: x_arl"""
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        return models.execute_kw(
            database, uid, password,
            'x_arl', 'search_read',
            [[]],
            {'fields': ['x_name', 'id']}
        )
    except Exception as e:
        logger.error("Error al obtener x_arl", exc_info=True)
        return []

def fetch_x_afp():
    """Modelo AFP: x_afp"""
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        return models.execute_kw(
            database, uid, password,
            'x_afp', 'search_read',
            [[]],
            {'fields': ['x_name', 'id']}
        )
    except Exception as e:
        logger.error("Error al obtener x_afp", exc_info=True)
        return []

def fetch_x_banco():
    """Modelo BANCO: x_banco"""
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        return models.execute_kw(
            database, uid, password,
            'x_banco', 'search_read',
            [[]],
            {'fields': ['x_name', 'id']}
        )
    except Exception as e:
        logger.error("Error al obtener x_banco", exc_info=True)
        return []

def fetch_x_centro_costos():
    """Modelo CENTRO COSTOS: x_centro_costos"""
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        return models.execute_kw(
            database, uid, password,
            'x_centro_costos', 'search_read',
            [[]],
            {'fields': ['x_name', 'id']}
        )
    except Exception as e:
        logger.error("Error al obtener x_centro_costos", exc_info=True)
        return []

def fetch_x_talla_camisa():
    """Modelo Talla Camisa: x_talla_camisa"""
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        return models.execute_kw(
            database, uid, password,
            'x_talla_camisa', 'search_read',
            [[]],
            {'fields': ['x_name', 'id']}
        )
    except Exception as e:
        logger.error("Error al obtener x_talla_camisa", exc_info=True)
        return []

def fetch_x_talla_calzado():
    """Modelo Talla Calzado: x_talla_calzado"""
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        return models.execute_kw(
            database, uid, password,
            'x_talla_calzado', 'search_read',
            [[]],
            {'fields': ['x_name', 'id']}
        )
    except Exception as e:
        logger.error("Error al obtener x_talla_calzado", exc_info=True)
        return []

def fetch_x_talla_pantalon():
    """Modelo Talla Pantalón: x_talla_pantalon"""
    uid = get_odoo_uid()
    if uid is None:
        return []
    models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
    try:
        return models.execute_kw(
            database, uid, password,
            'x_talla_pantalon', 'search_read',
            [[]],
            {'fields': ['x_name', 'id']}
        )
    except Exception as e:
        logger.error("Error al obtener x_talla_pantalon", exc_info=True)
        return []
