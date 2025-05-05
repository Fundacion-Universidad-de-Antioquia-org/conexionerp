# app_comprobantes/models.py
from django.db import models

class LaborCertificate(models.Model):
    comprobante_date = models.DateField(verbose_name="Fecha del comprobante")
    company = models.CharField(max_length=255, verbose_name="Compañía")
    cedula = models.CharField(max_length=50, null=True, blank=True, verbose_name="Cédula")
    blob_url = models.URLField(max_length=500, verbose_name="URL del Blob")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Subido el")
    observations = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.company} - {self.cedula}"
    
class CIRCertificate(models.Model):
    comprobante_date = models.DateField()
    company = models.CharField(max_length=255)
    cedula = models.CharField(max_length=20)
    blob_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    observations = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"CIR {self.comprobante_date} - {self.company} - {self.cedula}"