import os
from urllib.parse import quote
import xmlrpc.client
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
database = os.getenv("DATABASE")
user = os.getenv("ODOO_USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")

def fetch_departametos_from_odoo():
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')
        logger.debug(f'Authenticated user ID:{uid}')
       
        departamentos = models.execute_kw(database, uid, password,
            'hr.department', 'search_read',
            [[]],  # Filtrar si es necesario
            {'fields': ['name']})
 
        if departamentos:
            logger.debug(f'Retrieved {len(departamentos)} departamentos')
        else:
            logger.debug('No deparments found')
        # print("Departamentos: ", departamentos)
        return [departamento['name'] for departamento in departamentos if 'name' in departamento]
 
    except Exception as e:
        logger.error('Failed to fetch data from Odoo', exc_info=True)
        return []
