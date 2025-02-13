# app_comprobantes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload_comprobantes/', views.certificate_upload, name='certificate_upload'),
    # Puedes definir una vista o template para el éxito
    path('consultar_comprobantes/', views.certificates_by_cedula, name='certificates_by_cedula'),
    path('api/certificates/', views.get_certificate_by_cedula, name='api_certificates'),
    path('upload_cir/', views.cir_upload, name='cir_upload'),
    # Puedes definir una vista o template para el éxito
    path('consultar_cir/', views.cir_by_cedula, name='cir_by_cedula'),
    path('api/cir/', views.get_cir_by_cedula, name='api_cIR'),
    path("delete_cir/", views.delete_cir, name="delete_cir"),
    path("download_cir/", views.download_cir, name="download_cir"),
    path("delete_comprobantes/", views.delete_certificates, name="delete_certificates"),
    path("download_comprobantes/", views.download_certificates, name="download_certificates"),
    path("home/", views.home, name="home"),

    
]
