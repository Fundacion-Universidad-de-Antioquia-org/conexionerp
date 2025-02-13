# app_comprobantes/forms.py
from django import forms

class CertificateUploadForm(forms.Form):
    comprobante_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Fecha de comprobantes"
    )
    company = forms.CharField(max_length=255, label="Compañía")
    zip_file = forms.FileField(label="Archivo ZIP")
    observations = forms.CharField(label="Descripción")
class CIRUploadForm(forms.Form):
    comprobante_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    company = forms.CharField(max_length=255)
    zip_file = forms.FileField()
    observations = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
