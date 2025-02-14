# app_comprobantes/views.py

import zipfile
import re
import xmlrpc.client
from django.views.decorators.csrf import csrf_exempt
import io  # ✅ Importa el módulo IO para manejar archivos en memoria
import requests
import logging
from django.http import HttpResponse,JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.conf import settings
from .forms import CertificateUploadForm,CIRUploadForm
from .models import LaborCertificate,CIRCertificate
import base64  # <--- Asegúrate de tener esta línea
from django.shortcuts import render
from .models import LaborCertificate
from django.views.decorators.http import require_GET
from django.db.models import Count
import datetime
import logging
import os,json
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContentSettings


load_dotenv()
logger = logging.getLogger(__name__)
# Importa el cliente de Azure Blob Storage
database = os.getenv("DATABASE")
user = os.getenv("ODOO_USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
@settings.AUTH.login_required
def index(request, *, context):
    user = context['user']
    return HttpResponse(f"Hello, {user.get('name')}.")

@settings.AUTH.login_required()
def certificate_upload(request, *, context):
    error_messages = []
    success_message = None

    if request.method == 'POST':
        form = CertificateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            comprobante_date = form.cleaned_data['comprobante_date']
            company = form.cleaned_data['company']
            zip_file = request.FILES['zip_file']
            observations = form.cleaned_data['observations']

            extracted_files = {}
            # Validar archivos dentro del ZIP y extraer las cédulas antes de subir a Azure
            try:
                with zipfile.ZipFile(zip_file) as z:
                    for file_info in z.infolist():
                        if file_info.filename.lower().endswith('.pdf'):
                            match = re.search(r'-(\d{7,10})\.pdf$', file_info.filename)
                            if not match:
                                error_messages.append(f"Formato incorrecto en: {file_info.filename}")
                                continue

                            cedula = match.group(1)  # Extrae la cédula correctamente

                            # 🔴 Nuevo identificador único: combinación de fechas y cédula
                            file_key = f"{file_info.filename.split('-')[0]}-{file_info.filename.split('-')[1]}-{cedula}"

                            if file_key in extracted_files:
                                error_messages.append(f"Archivo duplicado en ZIP: {file_info.filename}")
                                continue

                            extracted_files[file_key] = {  # Se usa file_key para validar duplicados, pero guardamos cédula
                                'filename': file_info.filename,
                                'data': z.read(file_info),
                                'cedula': cedula  # Agregamos la cédula separadamente
                            }


            except zipfile.BadZipFile:
                return JsonResponse({"success": False, "error": "El archivo ZIP no es válido."}, status=400)

            if error_messages:
                return JsonResponse({"success": False, "error": "Algunos archivos tienen formato incorrecto o están duplicados."}, status=400)

            # Inicializar cliente de Azure
            connection_string = settings.AZURE_CONNECTION_STRING
            container_name = settings.AZURE_CONTAINER
            try:
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                container_client = blob_service_client.get_container_client(container_name)
            except Exception as e:
                return JsonResponse({"success": False, "error": "Error conectando con Azure Blob Storage."}, status=400)

            success_count = 0
            
            # Subir archivos a Azure y registrar en BD
            for file_key, file_info in extracted_files.items():
                blob_name = file_info['filename'].split('/')[-1]
                blob_client = container_client.get_blob_client(blob_name)

                try:
                    blob_client.upload_blob(file_info['data'], overwrite=True, content_settings=ContentSettings(content_type='application/pdf'))
                    blob_url = blob_client.url
                except Exception as e:
                    return JsonResponse({"success": False, "error": f"Error subiendo {file_info['filename']}"}, status=400)

                try:
                    certificate = LaborCertificate(
                        comprobante_date=comprobante_date,
                        company=company,
                        cedula=file_info['cedula'],  # 🔴 Guardamos SOLO la cédula en la BD
                        observations=observations,
                        blob_url=blob_url
                    )
                    certificate.save()
                    success_count += 1
                except Exception as e:
                    return JsonResponse({"success": False, "error": f"Error guardando registro para {file_info['filename']}"}, status=400)

            return JsonResponse({"success": True, "message": f"Se cargaron correctamente {success_count} archivos."})
    
    form = CertificateUploadForm()
    companies = fetch_companies_from_odoo()
    success_message = request.GET.get("success")

    return render(request, 'app_comprobantes/upload_certificate.html', {
        'form': form,
        'companies': companies,
        'success_message': success_message
    })

# Función para obtener compañías desde Odoo (se usa solo el campo name)
def fetch_companies_from_odoo():
    try:
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(database, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        companies = models.execute_kw(
            database, uid, password,
            'res.company', 'search_read',
            [[]],  # Sin filtro para traer todas
            {'fields': ['name']}
        )

        if not companies:
            logger.debug('No se encontraron compañías en Odoo.')
            return []
        
        # Retorna una lista de diccionarios con solo el campo name.
        return [{'name': company.get('name', '')} for company in companies]

    except Exception as e:
        logger.error('Error al obtener datos de compañías desde Odoo', exc_info=True)
        return []

def upload_success(request):
    return HttpResponse("¡Comprobantes subidos y procesados exitosamente!")
# app_comprobantes/views.py

@settings.AUTH.login_required()
def certificates_by_cedula(request, *, context):
    cedula = request.GET.get('cedula', None)
    company = request.GET.get('company', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    certificates = LaborCertificate.objects.all()
    if cedula:
        certificates = certificates.filter(cedula=cedula)
    if company:
        certificates = certificates.filter(company__icontains=company)
    if start_date:
        certificates = certificates.filter(comprobante_date__gte=start_date)
    if end_date:
        certificates = certificates.filter(comprobante_date__lte=end_date)

    context = {
        'cedula': cedula,
        'company': company,
        'start_date': start_date,
        'end_date': end_date,
        'certificates': certificates
    }
    return render(request, 'app_comprobantes/certificates_by_cedula.html', context)

@csrf_exempt
def delete_certificates(request):
    """
    Elimina certificados CIR tanto de Azure como de la base de datos.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        ids = data.get("ids", [])

        if not ids:
            return JsonResponse({"success": False, "error": "No se proporcionaron IDs para eliminar"}, status=400)

        connection_string = settings.AZURE_CONNECTION_STRING
        container_name = settings.AZURE_CONTAINER
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        success_count = 0
        error_messages = []

        for cert_id in ids:
            try:
                # Obtener certificado de la BD
                cert = LaborCertificate.objects.get(id=cert_id)
                blob_url = cert.blob_url

                if not blob_url:
                    error_messages.append(f"Certificado {cert_id} no tiene una URL válida.")
                    continue

                # Extraer el nombre del blob desde la URL sin repetir el contenedor
                parsed_url = urlparse(blob_url)
                blob_name = unquote(parsed_url.path.lstrip("/"))  # Decodifica caracteres especiales

                # Eliminar el prefijo del contenedor si está duplicado
                if blob_name.startswith(f"{container_name}/"):
                    blob_name = blob_name[len(f"{container_name}/"):]

                logger.info(f"Intentando eliminar blob: {blob_name}")

                # Verificar si el blob existe antes de eliminar
                blob_client = container_client.get_blob_client(blob_name)
                if not blob_client.exists():
                    error_messages.append(f"Blob no encontrado en Azure: {blob_name}")
                else:
                    # Eliminar el blob en Azure
                    blob_client.delete_blob()
                    logger.info(f"Blob eliminado exitosamente: {blob_name}")

                # Eliminar de la BD si la eliminación en Azure fue exitosa
                deleted_count, _ = LaborCertificate.objects.filter(id=cert_id).delete()
                if deleted_count > 0:
                    logger.info(f"Certificado {cert_id} eliminado de la BD.")
                    success_count += 1
                else:
                    error_messages.append(f"Certificado {cert_id} no se encontró en la BD.")

            except LaborCertificate.DoesNotExist:
                error_messages.append(f"Certificado con ID {cert_id} no encontrado en la BD.")
            except Exception as e:
                error_messages.append(f"Error eliminando certificado {cert_id}: {str(e)}")

        return JsonResponse({
            "success": True if success_count > 0 else False,
            "message": f"Se eliminaron {success_count} certificados exitosamente.",
            "error_messages": error_messages
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Error en el formato de los datos enviados"}, status=400)


def download_certificates(request):
    ids = request.GET.getlist("ids")

    if not ids:
        return JsonResponse({"success": False, "error": "No se seleccionaron certificados."}, status=400)

    certificates = LaborCertificate.objects.filter(id__in=ids)

    if not certificates:
        return JsonResponse({"success": False, "error": "No se encontraron certificados con los IDs seleccionados."}, status=404)

    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for cert in certificates:
            try:
                # ✅ Descarga el archivo directamente desde la URL almacenada en la BD
                response = requests.get(cert.blob_url, stream=True)

                if response.status_code == 200:
                    filename = f"{cert.cedula}.pdf"
                    zf.writestr(filename, response.content)
                else:
                    return JsonResponse(
                        {"success": False, "error": f"Error descargando el archivo {cert.blob_url}"},
                        status=404
                    )
            except Exception as e:
                return JsonResponse({"success": False, "error": f"Error al procesar {cert.blob_url}: {str(e)}"}, status=500)

    memory_file.seek(0)

    response = HttpResponse(memory_file, content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="comprobantes.zip"'

    return response

@require_GET
def get_certificate_by_cedula(request):

    cedula = request.GET.get('cedula')
    if not cedula:
        return JsonResponse({'error': 'No se proporcionó la cédula.'}, status=400)

    # Filtra los certificados que coincidan con la cédula
    certificates = LaborCertificate.objects.filter(cedula=cedula)

    # Serializa los datos en una lista de diccionarios
    data = []
    for cert in certificates:
        data.append({
            'id': cert.id,
            'comprobante_date': cert.comprobante_date.strftime('%Y-%m-%d'),
            'company': cert.company,
            'cedula': cert.cedula,
            'blob_url': cert.blob_url,
            'observations':cert.observations,
            'uploaded_at': cert.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    # Devuelve la lista dentro de un objeto JSON
    return JsonResponse({'certificates': data}, safe=False)

@settings.AUTH.login_required()
def cir_upload(request, *, context):
    error_messages = []
    success_message = None

    if request.method == 'POST':
        form = CIRUploadForm(request.POST, request.FILES)
        if form.is_valid():
            comprobante_date = form.cleaned_data['comprobante_date']
            company = form.cleaned_data['company']
            zip_file = request.FILES['zip_file']
            observations = form.cleaned_data['observations']

            extracted_files = {}

            logger.info(f"Procesando archivo CIR para fecha: {comprobante_date}, compañía: {company}")

           # Validar archivos dentro del ZIP y extraer las cédulas antes de subir a Azure
            try:
                with zipfile.ZipFile(zip_file) as z:
                    for file_info in z.infolist():
                        if file_info.filename.lower().endswith('.pdf'):
                            match = re.search(r'CIR (\d{4}) (.+)-(\d{7,10})\.pdf$', file_info.filename)
                            if not match:
                                error_messages.append(f"Formato incorrecto en: {file_info.filename}")
                                continue

                            year = match.group(1)  # Extrae el año (2024, 2025, etc.)
                            full_name = match.group(2).strip()  # Extrae el nombre completo
                            cedula = match.group(3)  # Extrae la cédula

                            # 🔴 Nuevo identificador único basado en Año + Nombre + Cédula
                            file_key = f"{year}-{full_name}-{cedula}"

                            if file_key in extracted_files:
                                error_messages.append(f"Archivo duplicado en ZIP: {file_info.filename}")
                                continue

                            extracted_files[file_key] = {  # Se usa file_key para evitar duplicados
                                'filename': file_info.filename,
                                'data': z.read(file_info),
                                'cedula': cedula  # Guardamos la cédula por separado para la BD
                            }

            except zipfile.BadZipFile:
                return JsonResponse({"success": False, "error": "El archivo ZIP no es válido."}, status=400)

            if error_messages:
                return JsonResponse({"success": False, "error": "Algunos archivos tienen formato incorrecto o están duplicados."}, status=400)

            # Inicializar cliente de Azure para CIR
            connection_string = settings.AZURE_CONNECTION_STRING
            container_name = settings.AZURE_CONTAINER_CIR
            try:
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                container_client = blob_service_client.get_container_client(container_name)
            except Exception as e:
                return JsonResponse({"success": False, "error": "Error conectando con Azure Blob Storage."}, status=400)

            success_count = 0
            
            # Subir archivos a Azure y registrar en BD
            for file_key, file_info in extracted_files.items():
                blob_name = file_info['filename'].split('/')[-1]
                blob_client = container_client.get_blob_client(blob_name)

                try:
                    blob_client.upload_blob(file_info['data'], overwrite=True, content_settings=ContentSettings(content_type='application/pdf'))
                    blob_url = blob_client.url
                except Exception as e:
                    return JsonResponse({"success": False, "error": f"Error subiendo {file_info['filename']}"}, status=400)

                try:
                    certificate = CIRCertificate(
                        comprobante_date=comprobante_date,
                        company=company,
                        cedula=file_info['cedula'],  # 🔴 Guardamos SOLO la cédula en la BD
                        observations=observations,
                        blob_url=blob_url
                    )
                    certificate.save()
                    success_count += 1
                except Exception as e:
                    return JsonResponse({"success": False, "error": f"Error guardando registro para {file_info['filename']}"}, status=400)

            return JsonResponse({"success": True, "message": f"Se cargaron correctamente {success_count} archivos."})
    
    form = CIRUploadForm()
    companies = fetch_companies_from_odoo()
    success_message = request.GET.get("success")

    return render(request, 'app_comprobantes/cir_upload.html', {
        'form': form,
        'companies': companies,
        'success_message': success_message
    })
    
@settings.AUTH.login_required()
def cir_by_cedula(request, *, context):
    cedula = request.GET.get('cedula', None)
    company = request.GET.get('company', None)
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)

    certificates = CIRCertificate.objects.all()

    if cedula:
        certificates = certificates.filter(cedula=cedula)
    if company:
        certificates = certificates.filter(company__icontains=company)
    if date_from:
        certificates = certificates.filter(comprobante_date__gte=date_from)
    if date_to:
        certificates = certificates.filter(comprobante_date__lte=date_to)

    context = {
        'cedula': cedula,
        'company': company,
        'date_from': date_from,
        'date_to': date_to,
        'certificates': certificates
    }
    return render(request, 'app_comprobantes/cir_by_cedula.html', context)

@require_GET
def get_cir_by_cedula(request):
    """
    Endpoint que, dado el parámetro 'cedula', devuelve los registros de certificados CIR asociados.
    Ejemplo de uso:
        GET /api/cir_certificates/?cedula=15274755
    """
    cedula = request.GET.get('cedula')
    if not cedula:
        return JsonResponse({'error': 'No se proporcionó la cédula.'}, status=400)

    certificates = CIRCertificate.objects.filter(cedula=cedula)

    data = []
    for cert in certificates:
        data.append({
            'id': cert.id,
            'comprobante_date': cert.comprobante_date.strftime('%Y-%m-%d'),
            'company': cert.company,
            'cedula': cert.cedula,
            'blob_url': cert.blob_url,
            'observations': cert.observations,
            'uploaded_at': cert.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    return JsonResponse({'certificates': data}, safe=False)

@csrf_exempt
def delete_cir(request):
    """
    Elimina certificados CIR tanto de Azure como de la base de datos.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        ids = data.get("ids", [])

        if not ids:
            return JsonResponse({"success": False, "error": "No se proporcionaron IDs para eliminar"}, status=400)

        connection_string = settings.AZURE_CONNECTION_STRING
        container_name = settings.AZURE_CONTAINER_CIR
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        success_count = 0
        error_messages = []

        for cert_id in ids:
            try:
                # Obtener certificado de la BD
                cert = CIRCertificate.objects.get(id=cert_id)
                blob_url = cert.blob_url

                if not blob_url:
                    error_messages.append(f"Certificado {cert_id} no tiene una URL válida.")
                    continue

                # Extraer el nombre del blob desde la URL sin repetir el contenedor
                parsed_url = urlparse(blob_url)
                blob_name = unquote(parsed_url.path.lstrip("/"))  # Decodifica caracteres especiales

                # Eliminar el prefijo del contenedor si está duplicado
                if blob_name.startswith(f"{container_name}/"):
                    blob_name = blob_name[len(f"{container_name}/"):]

                logger.info(f"Intentando eliminar blob: {blob_name}")

                # Verificar si el blob existe antes de eliminar
                blob_client = container_client.get_blob_client(blob_name)
                if not blob_client.exists():
                    error_messages.append(f"Blob no encontrado en Azure: {blob_name}")
                else:
                    # Eliminar el blob en Azure
                    blob_client.delete_blob()
                    logger.info(f"Blob eliminado exitosamente: {blob_name}")

                # Eliminar de la BD si la eliminación en Azure fue exitosa
                deleted_count, _ = CIRCertificate.objects.filter(id=cert_id).delete()
                if deleted_count > 0:
                    logger.info(f"Certificado {cert_id} eliminado de la BD.")
                    success_count += 1
                else:
                    error_messages.append(f"Certificado {cert_id} no se encontró en la BD.")

            except CIRCertificate.DoesNotExist:
                error_messages.append(f"Certificado con ID {cert_id} no encontrado en la BD.")
            except Exception as e:
                error_messages.append(f"Error eliminando certificado {cert_id}: {str(e)}")

        return JsonResponse({
            "success": True if success_count > 0 else False,
            "message": f"Se eliminaron {success_count} certificados exitosamente.",
            "error_messages": error_messages
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Error en el formato de los datos enviados"}, status=400)


def download_cir(request):
    ids = request.GET.getlist("ids")

    if not ids:
        return JsonResponse({"success": False, "error": "No se seleccionaron certificados."}, status=400)

    certificates = CIRCertificate.objects.filter(id__in=ids)

    if not certificates:
        return JsonResponse({"success": False, "error": "No se encontraron certificados con los IDs seleccionados."}, status=404)

    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for cert in certificates:
            try:
                # ✅ Descarga el archivo directamente desde la URL almacenada en la BD
                response = requests.get(cert.blob_url, stream=True)

                if response.status_code == 200:
                    filename = f"{cert.cedula}.pdf"
                    zf.writestr(filename, response.content)
                else:
                    return JsonResponse(
                        {"success": False, "error": f"Error descargando el archivo {cert.blob_url}"},
                        status=404
                    )
            except Exception as e:
                return JsonResponse({"success": False, "error": f"Error al procesar {cert.blob_url}: {str(e)}"}, status=500)

    memory_file.seek(0)

    response = HttpResponse(memory_file, content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="certificados.zip"'
    return response

@settings.AUTH.login_required()
def home(request, *, context):
    month = request.GET.get('month')
    year = request.GET.get('year')

    # Convertimos los valores a enteros si existen
    month = int(month) if month else None
    year = int(year) if year else None

    # Obtener la lista de años disponibles
    current_year = datetime.datetime.now().year
    years = list(range(current_year, current_year - 5, -1))  # Últimos 5 años

    # Obtener la lista de meses
    months = [
        {"name": "Enero", "value": 1},
        {"name": "Febrero", "value": 2},
        {"name": "Marzo", "value": 3},
        {"name": "Abril", "value": 4},
        {"name": "Mayo", "value": 5},
        {"name": "Junio", "value": 6},
        {"name": "Julio", "value": 7},
        {"name": "Agosto", "value": 8},
        {"name": "Septiembre", "value": 9},
        {"name": "Octubre", "value": 10},
        {"name": "Noviembre", "value": 11},
        {"name": "Diciembre", "value": 12},
    ]

    # Construir el filtro dinámicamente
    certificate_query = LaborCertificate.objects.values('company')
    comprobante_query = CIRCertificate.objects.values('company')

    filters = {}
    if year:
        filters["comprobante_date__year"] = year  # Si hay año, filtrar por año
    if month:
        filters["comprobante_date__month"] = month  # Si hay mes, filtrar por mes

    if filters:
        certificate_query = certificate_query.filter(**filters)
        comprobante_query = comprobante_query.filter(**filters)

    # Obtener conteo de certificados por compañía
    certificate_stats = (
        certificate_query
        .annotate(total_certificates=Count('id'))
        .filter(total_certificates__gt=0)
    )

    # Obtener conteo de comprobantes por compañía
    comprobante_stats = (
        comprobante_query
        .annotate(total_comprobantes=Count('id'))
        .filter(total_comprobantes__gt=0)
    )

    return render(request, 'app_comprobantes/home.html', {
        'certificate_stats': certificate_stats,
        'comprobante_stats': comprobante_stats,
        'months': months,
        'years': years,
        'selected_month': month,
        'selected_year': year
    })    